"""
Medicine Wheel Gate Component for Langflow

Evaluates text through Medicine Wheel balance analysis — checks whether
all Four Directions are represented and flags ceremony requirements.
"""

from prompt_decomposition import (
    DirectionalDecomposer,
    MedicineWheelBridge,
)
from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output
from lfx.inputs.inputs import BoolInput, DropdownInput, SliderInput
from lfx.schema.message import Message


class MedicineWheelGateComponent(Component):
    display_name = "Medicine Wheel Gate"
    description = (
        "Evaluates text through Medicine Wheel balance analysis. "
        "Checks whether all Four Directions (EAST/SOUTH/WEST/NORTH) are represented, "
        "flags ceremony requirements, and provides relational guidance."
    )
    icon = "shield"
    name = "MedicineWheelGate"

    inputs = [
        MessageTextInput(
            name="text",
            display_name="Text",
            info="The text to evaluate for relational balance.",
            required=True,
        ),
        DropdownInput(
            name="gate_mode",
            display_name="Gate Mode",
            info="Advisory provides guidance; Enforce blocks unbalanced outputs.",
            options=["advisory", "enforce"],
            value="advisory",
        ),
        SliderInput(
            name="balance_threshold",
            display_name="Balance Threshold",
            info="Minimum balance score (0-1) to pass the gate.",
            value=0.4,
            range_spec={"min": 0.0, "max": 1.0, "step": 0.05},
        ),
        SliderInput(
            name="neglect_threshold",
            display_name="Neglect Threshold",
            info="Maximum number of neglected directions allowed.",
            value=1,
            range_spec={"min": 0, "max": 3, "step": 1},
        ),
        BoolInput(
            name="include_guidance",
            display_name="Include Guidance",
            info="Whether to include relational guidance in the output.",
            value=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Gate Result",
            name="gate_result",
            method="evaluate_balance",
        ),
    ]

    def evaluate_balance(self) -> Message:
        text = self.text
        if hasattr(text, "text"):
            text = text.text

        decomposer = DirectionalDecomposer()
        bridge = MedicineWheelBridge(ceremony_threshold=self.balance_threshold)

        analysis = decomposer.decompose(text)
        enriched = bridge.enrich(analysis)

        lines = []
        lines.append(f"## Medicine Wheel Gate — {'ADVISORY' if self.gate_mode == 'advisory' else 'ENFORCE'}")
        lines.append(f"**Balance Score:** {analysis.balance:.0%}")
        lines.append(f"**Lead Direction:** {analysis.lead_direction.value.upper()}")
        lines.append(f"**Ceremony Required:** {'Yes ⚠️' if enriched.ceremony_required else 'No ✅'}")

        if analysis.neglected_directions:
            dirs = ", ".join(d.value.upper() for d in analysis.neglected_directions)
            lines.append(f"**Neglected Directions:** {dirs}")

        passed = (
            analysis.balance >= self.balance_threshold
            and len(analysis.neglected_directions) <= int(self.neglect_threshold)
        )

        if self.gate_mode == "enforce" and not passed:
            lines.append("\n🛑 **GATE BLOCKED** — Relational balance requirements not met.")
        elif not passed:
            lines.append("\n⚠️ **GATE WARNING** — Consider improving balance.")
        else:
            lines.append("\n✅ **GATE PASSED** — Relational balance is adequate.")

        if self.include_guidance:
            guidance = bridge.get_relational_guidance(analysis)
            if guidance:
                lines.append("\n### Relational Guidance")
                for g in guidance:
                    lines.append(f"- {g}")

        output = "\n".join(lines)
        self.status = output
        return Message(text=output)
