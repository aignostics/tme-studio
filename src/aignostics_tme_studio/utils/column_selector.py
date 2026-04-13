"""Helper module to select columns from the dataframe using marimo UI functions."""

import string

import marimo as mo
import pandas as pd

from aignostics_tme_studio.utils import utils
from aignostics_tme_studio.utils.data_classes import Statistic
from aignostics_tme_studio.utils.ui_constants import ALL_TISSUES, DROPDOWN_LABELS


def _replace_column_headers(df: pd.DataFrame, columns_map: dict[str, str]) -> pd.DataFrame:
    """Replace column headers, keeping "grouping" column intact if it exists.

    Args:
        df: Source DataFrame to extract columns from.
        columns_map: Dictionary with column header mapping.

    Returns:
        The dataframe with replaced column headers, and `grouping` column if it existed in the original dataframe.
    """
    columns = list(columns_map.keys())
    return df[columns].rename(columns=columns_map)


def _stats_to_dropdown(stats: list[Statistic], label: str) -> mo.ui.dropdown:
    """Create a dropdown from a statistics dictionary.

    Args:
        stats: The list of statistics (pretty-print) with names and associated dataframe column
            header formatting strings.
        label: Label to print next to the dropdown.

    Returns:
        Dropdown to select the statistic.
    """
    return mo.ui.dropdown(
        options={stat.name: stat.formatter for stat in stats},
        label=label,
        value=next(iter(stats)).name,
    )


class FeatureColumnSelector:
    """Feature column selector.

    Helper class that is given a list of statistics, and provides a list of dropdowns to fill placeholders in the
    statistics. When the dropdown values are passed back to the class, it selects the appropriate TME feature columns
    by formatting the selected statistic with the provided values.
    When a placeholder is selected as "x_variable", all possible values for that placeholder are used to select a set of
    feature columns.

    Example:
        Our statistics are ["DENSITY_{cell_cls}_IN_{tissue_cls}", "RATIO_{cell_cls}_IN_{tissue_cls}"].
    We set "cell_cls" to be our `x_variable`.
    1. **creating dropdowns**: The `FeatureColumnSelector` sees the `cell_cls` and `tissue_cls` placeholders and creates
       dropdowns.
       In this case we would create two dropdowns: one to select from the list of statistics, and one to select from all
       available tissue classes to fill the `tissue_cls` placeholder. Since "cell_cls" is our `x_variable`, no dropdown
       is created for `cell_cls`.
    2. **selecting columns**: The user selects statistic: `"DENSITY_{cell_cls}_IN_{tissue_cls}"` and
       `tissue_cls`: `"Stroma"`.
       The `FeatureColumnSelector` formats the statistic to `"DENSITY_{cell_cls}_IN_STROMA"` and will then loop over all
       possible values for `cell_cls` to find the set of columns:
       ["DENSITY_LYMPHOCYTES_IN_STROMA", "DENSITY_FIBROBLASTS_IN_STROMA", etc. ]
    """

    def __init__(
        self, statistics: list[Statistic], x_variable: str, model_output_class_config: dict[str, list[str]]
    ) -> None:
        """Init feature column selector section.

        Args:
            statistics: List of statistics to select from, with formatting strings containing placeholders, e.g.
                "density_{cell_cls}_in_{tissue_cls}".
                Note: each statistic in the list should be of the same type, meaning,
                contain the same set of placeholders.
            x_variable: The placeholder that should be used as x variable in the plot, and for
                which the columns should be found by formatting with all possible values.
                Example: "cell_cls"; in which case columns will be found for all possible cell classes.
            model_output_class_config: Dictionary mapping placeholders to possible values, used to format the statistic
                formatter strings and find the columns in the dataframe.
        """
        self.statistics = statistics
        self.x_variable = x_variable

        self.placeholders = self._extract_placeholders()
        self.model_output_classes = model_output_class_config

        self.dropdowns = self._create_dropdowns()

    def render_dropdowns(self) -> mo.Html:
        """Render dropdowns.

        Returns:
            Marimo form containing the section header and all dropdowns in the section.
        """
        text = "<br>".join([f"{{{key}}}" for key in self.dropdowns])
        md = mo.md(text)
        return md.batch(**self.dropdowns)

    def extract_feature_columns(
        self, df: pd.DataFrame, grouping_column: str | None = None, **dropdown_args
    ) -> pd.DataFrame:
        """Extract feature columns with nicely formatted column headers.

        Args:
            df: the dataframe from which to extract columns.
            grouping_column: name of column by which data will be grouped in plots.
                This should be returned as-is.
            **dropdown_args: values selected by user using the dropdowns created by
                `render_dropdowns()`.

        Returns:
            The dataframe with only the selected feature columns and nicely formatted headers.
        """
        columns_map = self._create_column_mapping(**dropdown_args)
        # Keep grouping column in the df by adding an identity mapping
        if grouping_column:
            columns_map[grouping_column] = grouping_column

        return _replace_column_headers(df, columns_map=columns_map)

    def _create_column_mapping(self, **dropdown_args) -> dict[str, str]:
        """Create dictionary of feature columns to pretty-print column headers.

        Args:
            **dropdown_args: values selected by user using the dropdowns.

        Returns:
            Mapping from raw column name to pretty-print label,
            e.g. {"DENSITY_CELL_CARCINOMA_CELL": "Carcinoma cell", ...}.
        """
        # Format the statistic with the variables selected with the dropdowns
        column_format = self.get_column_format(dropdown_args)

        # Create one column mapping for each value available for `x_variable`
        if self.x_variable:
            x_values = self._get_model_output_classes_for_placeholder(self.x_variable)
            columns = {utils.to_allcaps(column_format.format(**{self.x_variable: b})): b for b in x_values}
        else:
            # No x_values to iterate over, just return the column itself
            columns = {utils.to_allcaps(column_format): column_format}

        return columns

    def _get_model_output_classes_for_placeholder(self, placeholder: str) -> list[str]:
        """Get model output classes for the given placeholder.

        We assume that:
        1. the placeholder is always in the format "{placeholder_name_<postfix>}"
        2. the dictionary of model_output_classes contains the placeholders as keys.

        E.g. for placeholder {cell_cls} we find the list of cell classes under the key 'cell_cls' in the dictionary.
        TODO: Give more concrete example?
        """
        # In case there are multiple placeholders with the same name they are differentiated by post-fixing them.
        # Just compare to the starting substring.
        if placeholder not in self.model_output_classes:
            placeholder = next(iter([k for k in self.model_output_classes if placeholder.startswith(k)]))
        return self.model_output_classes[placeholder]

    def _extract_placeholders(self) -> list[str]:
        """Extract placeholders that are in the (list of) statistic(s).

        We assume that all statistics have the same placeholders, so we only look at the first one.
        We also filter out the x variable, since that is not a dropdown we want to create.
        """
        placeholders = list(string.Formatter().parse(self.statistics[0].formatter))
        return [v[1] for v in placeholders if v[1] is not None and v[1] != self.x_variable]

    def _create_dropdowns(self) -> dict[str, mo.ui.dropdown]:
        """Create dropdowns to select statistics and values for each placeholder."""
        dropdowns = {"stat": _stats_to_dropdown(self.statistics, label=DROPDOWN_LABELS["stat"])}
        for key in self.placeholders:
            values = self._get_model_output_classes_for_placeholder(key)
            dropdowns[key] = mo.ui.dropdown(options=values, label=DROPDOWN_LABELS[key], value=next(iter(values)))
        return dropdowns

    def get_column_format(self, dropdown_args: dict[str, str]) -> str:
        """Get statistic formatter string with all placeholders filled except for `x_variable`.

        Args:
            dropdown_args: values selected by the user, keyed by dropdown name.
                The "stat" key is consumed to retrieve the formatter string.

        Returns:
            Formatter string with all placeholders resolved except for `x_variable`,
            which remains as a format placeholder for later iteration.
        """
        # Extract the formatter string for the statistic to plot, e.g. "density_{cell_cls}"
        statistic = dropdown_args.pop("stat")

        format_args = {key: dropdown_args.pop(key) for key in self.placeholders}
        # Identity mapping for x_variable to be formatted later
        format_args[self.x_variable] = f"{{{self.x_variable}}}"
        return statistic.format(**format_args)


class NoAnucleatedAreasFeatureColumnSelector(FeatureColumnSelector):
    """Wrapper around FeatureColumnSelector with some custom functionality.

    This does not allow selection of anucleated areas ("blood"/"necrosis") in the tissue type dropdowns.
    """

    def _get_model_output_classes_for_placeholder(self, placeholder: str) -> list[str]:
        """Get model output classes for the given placeholder.

        Remove anucleated areas for these stats.
        """
        output_classes = super()._get_model_output_classes_for_placeholder(placeholder)

        if placeholder == "tissue_cls":
            output_classes = [c for c in output_classes if c not in ["Blood", "Necrosis"]]
        return output_classes


class CellInTissueFeatureColumnSelector(NoAnucleatedAreasFeatureColumnSelector):
    """Wrapper around FeatureColumnSelector with some custom functionality.

    This extractor extracts Cells-inside-tissue stats.

    - Cells-in-tissue stats are not available for anucleated areas and thus these must be filtered out
    - Allow "All tissue" option that removes the "_{tissue_cls}" column postfix
    """

    def _create_dropdowns(self):
        dropdowns = super()._create_dropdowns()
        dropdowns["tissue_cls"] = mo.ui.dropdown(
            options={ALL_TISSUES: None} | dropdowns["tissue_cls"].options,
            allow_select_none=False,
            value=ALL_TISSUES,
            label=DROPDOWN_LABELS["tissue_cls"],
        )

        return dropdowns

    def get_column_format(self, *args, **kwargs) -> str:
        """Get statistic with filled placeholders and remove _None postfix if "All tissue types" is selected."""
        column = super().get_column_format(*args, **kwargs)
        # If no tissue was selected, we can still show the feature. We just need to remove "_NONE" at the end of the
        # columns.
        return column.removesuffix("_None")
