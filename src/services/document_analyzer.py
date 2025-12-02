"""
Document analysis and comment workflow service.
Handles document analysis, comment generation, and approval workflow.
"""

from typing import Dict, Optional
import questionary


class DocumentAnalyzer:
    """Service for analyzing documents and managing comment workflow."""

    def __init__(
        self,
        llm_service,
        context_manager,
        comment_poster,
        approval_workflow,
        document_monitor,
        terminal_ui
    ):
        """
        Initialize document analyzer.

        Args:
            llm_service: LLM service for analysis
            context_manager: Context file manager
            comment_poster: Service for posting comments
            approval_workflow: Approval workflow manager
            document_monitor: Document monitoring service
            terminal_ui: Terminal UI for user interactions
        """
        self.llm_service = llm_service
        self.context_manager = context_manager
        self.comment_poster = comment_poster
        self.approval_workflow = approval_workflow
        self.document_monitor = document_monitor
        self.terminal_ui = terminal_ui
        self.analysis_context: Optional[str] = None

    def analyze_document(self, doc_id: str, mode: str) -> None:
        """
        Analyze a single document with full approval workflow.

        Args:
            doc_id: Google Docs document ID
            mode: Analysis mode (outlier, summary, connect, question)
        """
        try:
            # Fetch document content
            print(f"📄 Fetching document: {doc_id}")
            doc_content = self.document_monitor.fetch_document_content(doc_id)

            # Extract text
            text = self.document_monitor.extract_text_from_document(doc_id)

            # Get context files
            context_files = self.context_manager.list_files()
            context_content = self.context_manager.get_concatenated_context() if context_files else ""

            # Build simple document structure for LLM (raw text, no conversion needed)
            document = {
                "document_id": doc_id,
                "text": text,  # Raw document text
                "context": context_content,  # Raw context text
                "analysis_situation": self.analysis_context  # Situational framing for analysis
            }

            # Perform LLM analysis
            context_status = " (with analysis context)" if self.analysis_context else ""
            print(f"🤖 Running {mode} analysis{context_status}...")
            result = self.llm_service.analyze(document, mode)

            if result:
                print(f"✅ Analysis complete")
                # Display mode-specific metrics
                if mode == "outlier":
                    percentile = result.get('outlier_percentile', 0.10)
                    print(f"   Ranking: Top {percentile*100:.0f}%")
                else:
                    print(f"   Confidence: {result.get('confidence', 0):.2f}")

                # Generate comment suggestion
                suggestion = self._generate_comment_suggestion(result, mode)

                # Handle approval workflow
                self._handle_approval_workflow(
                    doc_id, mode, result, suggestion, text, doc_content, document
                )

            else:
                print("⚠️  Analysis produced no results")

        except Exception as e:
            print(f"❌ Error analyzing document: {e}")

    def _handle_approval_workflow(
        self,
        doc_id: str,
        mode: str,
        result: Dict,
        suggestion: Dict,
        text: str,
        doc_content: Dict,
        document: Dict
    ) -> None:
        """Handle the approval workflow for a suggestion."""
        # Display suggestion to researcher
        print()
        print("=" * 70)
        print("📊 Suggested Comment:")
        print("─" * 70)

        # Show context if available
        target_text = result.get("target_text")
        if target_text:
            print(f"📍 Regarding: \"{target_text}\"")
            print()

        print(suggestion["comment_text"])
        print("─" * 70)
        print()

        # Get researcher decision (interactive menu)
        decision_input = self.terminal_ui.get_approval_decision()

        if decision_input == 'y':
            self._handle_approve(doc_id, mode, result, suggestion, text, doc_content)

        elif decision_input == 'e':
            self._handle_edit(doc_id, mode, result, suggestion, text, doc_content)

        elif decision_input == 'r':
            self._handle_refine(doc_id, mode, result, suggestion, text, doc_content, document)

        else:
            print("❌ Comment rejected")
            self.approval_workflow.process_decision(
                suggestion=suggestion,
                decision_type="reject",
                researcher_id="researcher"
            )

    def _handle_approve(
        self,
        doc_id: str,
        mode: str,
        result: Dict,
        suggestion: Dict,
        text: str,
        doc_content: Dict
    ) -> None:
        """Handle approve decision."""
        target_text = result.get("target_text")

        # Set document content for position finding
        if target_text:
            self.comment_poster.current_document_text = text
            self.comment_poster.current_document_structure = doc_content

        # Post comment
        comment_dict = {
            "document_id": doc_id,
            "comment_text": suggestion["comment_text"],
            "text_position": target_text,
            "mode": mode,
        }
        # Add mode-specific metrics
        if mode == "outlier":
            comment_dict["outlier_percentile"] = result.get("outlier_percentile", 0.10)
        else:
            comment_dict["confidence"] = result.get("confidence", 0)

        post_result = self.comment_poster.post_comment(comment_dict)

        if post_result.get("success"):
            print("✅ Comment posted successfully")
            print(f"   Comment ID: {post_result.get('comment_id')}")
        else:
            error_msg = post_result.get('message') or post_result.get('error') or 'Unknown error'
            print(f"⚠️  Comment posting failed: {error_msg}")

        self.approval_workflow.process_decision(
            suggestion=suggestion,
            decision_type="approve",
            researcher_id="researcher"
        )

    def _handle_edit(
        self,
        doc_id: str,
        mode: str,
        result: Dict,
        suggestion: Dict,
        text: str,
        doc_content: Dict
    ) -> None:
        """Handle edit decision."""
        print()
        edited_text = questionary.text(
            "Edit comment:",
            default=suggestion["comment_text"]
        ).ask()

        if edited_text and edited_text.strip():
            target_text = result.get("target_text")

            if target_text:
                self.comment_poster.current_document_text = text
                self.comment_poster.current_document_structure = doc_content

            comment_dict = {
                "document_id": doc_id,
                "comment_text": edited_text,
                "text_position": target_text,
                "mode": mode,
            }
            if mode == "outlier":
                comment_dict["outlier_percentile"] = result.get("outlier_percentile", 0.10)
            else:
                comment_dict["confidence"] = result.get("confidence", 0)

            post_result = self.comment_poster.post_comment(comment_dict)

            print()
            if post_result.get("success"):
                print("✅ Edited comment posted successfully")
                print(f"   Comment ID: {post_result.get('comment_id')}")
            else:
                error_msg = post_result.get('message') or post_result.get('error') or 'Unknown error'
                print(f"⚠️  Comment posting failed: {error_msg}")

            self.approval_workflow.process_decision(
                suggestion=suggestion,
                decision_type="edit",
                edited_text=edited_text,
                researcher_id="researcher"
            )
        else:
            print()
            print("❌ Empty comment, not posted")

    def _handle_refine(
        self,
        doc_id: str,
        mode: str,
        result: Dict,
        suggestion: Dict,
        text: str,
        doc_content: Dict,
        document: Dict
    ) -> None:
        """Handle refine decision."""
        print()
        instruction = questionary.text(
            "How should I modify the comment? (e.g., 'make it shorter', 'more encouraging'):"
        ).ask()

        if not instruction or not instruction.strip():
            print("❌ No instruction provided, keeping original comment")
            return

        print()
        print(f"🔄 Refining comment: \"{instruction}\"...")

        # Regenerate original mode-specific prompt with full document context
        template = self.llm_service.templates[mode]
        original_prompt = template.generate(document)

        # Append conversation history for iterative refinement
        refinement_prompt = f"""{original_prompt}

=== REFINEMENT REQUEST ===
Previous attempt: "{suggestion["comment_text"]}"
User feedback: {instruction}

Please refine the response according to the user's feedback while:
1. Maintaining all original requirements from the instructions above
2. Preserving relevance to the contributions and context
3. Applying the user's specific modification request

Return the same JSON structure as before with the refined content."""

        # Call LLM for refinement
        try:
            from google.generativeai import GenerativeModel
            import google.generativeai as genai

            genai.configure(api_key=self.llm_service.api_key)
            model = GenerativeModel(self.llm_service.model)

            response = model.generate_content(
                refinement_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                )
            )

            # Parse refinement result
            refined = self.llm_service._parse_structured_response(response.text)

            if refined and refined.get("refined_comment"):
                suggestion["comment_text"] = refined["refined_comment"]

                # Show refined comment
                print()
                print("=" * 70)
                print("🔄 Refined Comment:")
                print("─" * 70)
                print(suggestion["comment_text"])
                print("─" * 70)
                print()

                # Get new decision
                decision_input = self.terminal_ui.get_approval_decision()

                if decision_input == 'y':
                    self._post_refined_comment(
                        doc_id, mode, result, suggestion, text, doc_content, refined
                    )
                elif decision_input == 'e':
                    self._edit_refined_comment(
                        doc_id, mode, result, suggestion, text, doc_content, refined
                    )
                else:
                    print("❌ Refined comment rejected")
            else:
                print("⚠️  Failed to refine comment, using original")

        except Exception as e:
            print(f"❌ Refinement error: {e}")
            print("   Using original comment")

    def _post_refined_comment(
        self,
        doc_id: str,
        mode: str,
        result: Dict,
        suggestion: Dict,
        text: str,
        doc_content: Dict,
        refined: Dict
    ) -> None:
        """Post a refined comment."""
        target_text = result.get("target_text")
        if target_text:
            self.comment_poster.current_document_text = text
            self.comment_poster.current_document_structure = doc_content

        comment_dict = {
            "document_id": doc_id,
            "comment_text": suggestion["comment_text"],
            "text_position": target_text,
            "mode": mode,
            "confidence": refined.get("confidence", 0)
        }
        post_result = self.comment_poster.post_comment(comment_dict)

        if post_result.get("success"):
            print("✅ Refined comment posted successfully")
            print(f"   Comment ID: {post_result.get('comment_id')}")
        else:
            error_msg = post_result.get('message') or post_result.get('error') or 'Unknown error'
            print(f"⚠️  Comment posting failed: {error_msg}")

        self.approval_workflow.process_decision(
            suggestion=suggestion,
            decision_type="refine_approve",
            researcher_id="researcher"
        )

    def _edit_refined_comment(
        self,
        doc_id: str,
        mode: str,
        result: Dict,
        suggestion: Dict,
        text: str,
        doc_content: Dict,
        refined: Dict
    ) -> None:
        """Edit and post a refined comment."""
        edited_text = questionary.text(
            "Edit comment:",
            default=suggestion["comment_text"]
        ).ask()

        if edited_text and edited_text.strip():
            target_text = result.get("target_text")
            if target_text:
                self.comment_poster.current_document_text = text
                self.comment_poster.current_document_structure = doc_content

            comment_dict = {
                "document_id": doc_id,
                "comment_text": edited_text,
                "text_position": target_text,
                "mode": mode,
                "confidence": refined.get("confidence", 0)
            }
            post_result = self.comment_poster.post_comment(comment_dict)

            if post_result.get("success"):
                print("✅ Edited comment posted successfully")
                print(f"   Comment ID: {post_result.get('comment_id')}")
            else:
                error_msg = post_result.get('message') or post_result.get('error') or 'Unknown error'
                print(f"⚠️  Comment posting failed: {error_msg}")

    def _generate_comment_suggestion(self, analysis_result: Dict, mode: str) -> Dict:
        """Generate concise comment suggestion from analysis result."""
        if mode == "outlier":
            comment_text = analysis_result.get('encouragement_message', 'Great work!')

        elif mode == "summary":
            comment_text = analysis_result.get('summary', 'No summary available')

        elif mode == "connect":
            connections = analysis_result.get('connections', [])
            if connections:
                conn = connections[0]
                comment_text = conn.get('connection_message', 'Consider collaborating!')
            else:
                comment_text = "No connections found at this time."

        elif mode == "question":
            questions = analysis_result.get('clarifying_questions', [])
            comment_text = " ".join(questions) if questions else "No questions at this time."
        else:
            comment_text = "Analysis complete."

        suggestion = {
            "comment_text": comment_text,
            "mode": mode,
            "analysis_result": analysis_result
        }
        # Add mode-specific metrics
        if mode == "outlier":
            suggestion["outlier_percentile"] = analysis_result.get("outlier_percentile", 0.10)
        else:
            suggestion["confidence"] = analysis_result.get("confidence", 0)

        return suggestion
