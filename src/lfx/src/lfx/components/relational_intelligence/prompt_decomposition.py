"""
Prompt Decomposition Component for Langflow

Decomposes complex prompts through Four Directions analysis (Medicine Wheel),
extracting intents, mapping dependencies, and building ordered action stacks.
"""

from prompt_decomposition import (
    DirectionalDecomposer,
    IntentExtractor,
    DependencyMapper,
    ActionStackBuilder,
    MedicineWheelBridge,
    decompose,
)
from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output
from lfx.inputs.inputs import BoolInput, DropdownInput, IntInput, SliderInput
from lfx.schema.message import Message


class PromptDecompositionComponent(Component):
    display_name = "Prompt Decomposition"
    description = (
        "Decomposes complex prompts through Four Directions analysis "
        "(EAST=Vision, SOUTH=Analysis, WEST=Validation, NORTH=Action). "
        "Extracts intents, maps dependencies, and builds ordered action stacks."
    )
    icon = "compass"
    name = "PromptDecomposition"

    inputs = [
        MessageTextInput(
            name="prompt",
            display_name="Prompt",
            info="The prompt to decompose through Four Directions analysis.",
            required=True,
        ),
        DropdownInput(
            name="output_format",
            display_name="Output Format",
            info="Format for the decomposition output.",
            options=["json", "markdown", "action_stack"],
            value="json",
        ),
        BoolInput(
            name="extract_implicit",
            display_name="Extract Implicit Intents",
            info="Whether to detect implicit intents (e.g., 'needs testing' implies a test action).",
            value=True,
        ),
        IntInput(
            name="max_actions",
            display_name="Max Actions",
            info="Maximum number of actions in the output stack.",
            value=20,
        ),
        SliderInput(
            name="ceremony_threshold",
            display_name="Ceremony Threshold",
            info="Balance threshold below which ceremony pause is recommended (0-1).",
            value=0.3,
            range_spec={"min": 0.0, "max": 1.0, "step": 0.05},
        ),
    ]

    outputs = [
        Output(
            display_name="Decomposition",
            name="decomposition_output",
            method="run_decomposition",
        ),
    ]

    def run_decomposition(self) -> Message:
        prompt_text = self.prompt
        if hasattr(prompt_text, "text"):
            prompt_text = prompt_text.text

        result = decompose(
            prompt_text,
            extract_implicit=self.extract_implicit,
            max_items=self.max_actions,
            ceremony_threshold=self.ceremony_threshold,
        )

        if self.output_format == "markdown":
            output = result["markdown"]
        elif self.output_format == "action_stack":
            actions = result["decomposition"].action_stack
            lines = []
            for i, action in enumerate(actions, 1):
                lines.append(
                    f"{i}. [{action.direction.value.upper()}] {action.text} "
                    f"(confidence: {action.confidence:.0%})"
                )
            output = "\n".join(lines)
        else:
            output = result["json"]

        self.status = output
        return Message(text=output)
