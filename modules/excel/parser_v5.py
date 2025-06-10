import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

import numpy as np

from .excel_model_extension import ExcelModelFromBook
from .formulas.cell import Cell
from .formulas.tokens.operand import DeferredReference
from .formulas.errors import RangeValueError
import openpyxl

logger = logging.getLogger(__name__)


# Dataclasses remain the same.
@dataclass
class ParserConfig:
    pass


@dataclass
class ComputationReport:
    total_formulas: int = 0
    success_count: int = 0
    error_count: int = 0
    skipped_indirect: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        calculable_formulas = self.total_formulas - self.skipped_indirect
        if calculable_formulas == 0:
            return 100.0 if self.error_count == 0 else 0.0
        return (self.success_count / calculable_formulas) * 100


class ComplexExcelFormulaParser:
    def __init__(self, config: Optional[ParserConfig] = None):
        self.config = config or ParserConfig()

    def parse_and_apply(self, source_workbook_path: str) -> Tuple[openpyxl.Workbook, ComputationReport]:
        logger.info("Received source_workbook_path:" + source_workbook_path)
        model = ExcelModelFromBook().load(source_workbook_path).finish()

        iteration_count = 0
        while iteration_count < 10:
            iteration_count += 1
            print(f"--- Calculation Pass {iteration_count} ---")

            solution = model.calculate()

            recompile_map = {}
            for node_name, range_result in solution.items():
                try:
                    value_array = range_result.value
                    flat_results = value_array.ravel() if isinstance(value_array, np.ndarray) else [value_array]
                    for value in flat_results:
                        if isinstance(value, DeferredReference):
                            recompile_map[node_name] = str(value)
                except (AttributeError, RangeValueError):
                    continue

            if not recompile_map:
                print("\n--- No more deferred references found. Calculation is stable. ---")
                final_solution = solution
                break

            print(f"\nDiscovered {len(recompile_map)} cells to recompile: {recompile_map}\n")

            for original_name, target_name in recompile_map.items():
                print(f"Recompiling '{original_name}' with new formula '={target_name}'")

                if original_name not in model.cells:
                    logger.info(f"Cell '{original_name}' not found in model.cells, skipping recompilation.")
                    continue

                original_cell_obj = model.cells[original_name]
                if original_cell_obj.range is not None:
                    context = {
                        'directory': original_cell_obj.range.ranges[0]['directory'],
                        'filename': original_cell_obj.range.ranges[0]['filename'],
                        'sheet': original_cell_obj.range.ranges[0]['sheet'],
                    }

                    simple_reference = original_cell_obj.range.ranges[0]['ref']
                    new_formula = f"={target_name}"

                    new_cell = Cell(simple_reference, new_formula, context=context)

                else:
                    new_cell = original_cell_obj



                new_cell.compile(references=model.references).add(model.dsp)

                # Update the model's own dictionary of cells.
                model.cells[original_name] = new_cell
        else:
            print("\n--- ERROR: Hit maximum iteration limit. ---")
            final_solution = solution

        model.write(r"C:\Users\paulh\Downloads\computed")