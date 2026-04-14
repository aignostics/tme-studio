"""Tumor immune phenotype classification."""

from functools import cached_property
from typing import Literal

import numpy as np
import pandas as pd
from plotly import graph_objects as go

from aignostics_tme_studio.styling import styling_utils

COLUMN_DENSITY_STROMA = "CELL_DENSITY_LYMPHOCYTE_STROMA"
COLUMN_DENSITY_CARCINOMA = "CELL_DENSITY_LYMPHOCYTE_CARCINOMA"
COLUMN_RATIO_STROMA = "CELL_PERCENTAGE_LYMPHOCYTE_STROMA"
COLUMN_RATIO_CARCINOMA = "CELL_PERCENTAGE_LYMPHOCYTE_CARCINOMA"


IDE_COLORS = {
    "inflamed": styling_utils.aignx_pink,
    "excluded": styling_utils.aignx_green,
    "desert": styling_utils.aignx_blue,
}


class TIPClassifier:
    """Classifies slides into inflamed/desert/excluded classes."""

    def __init__(
        self,
        df: pd.DataFrame,
        carcinoma_thresh: float,
        stroma_thresh: float,
        metric: Literal["Density", "Percentage "] = "Density",
    ) -> None:
        """Initialize the Tumor Immune Phenotype (TIP) classifier.

        Args:
            df: The dataframe containing the expected columns with lymphocyte densities
                inside carcinoma and stroma regions.
            carcinoma_thresh: Slide is classified as inflamed if lymphocyte density
                inside carcinoma is above this value.
            stroma_thresh: Slide is classified as excluded if not inflamed, and
                lymphocyte density in stroma is above this value.
            metric: Metrics to use to determine presence of lymphocytes inside
                carcinoma and stroma regions. Supported values are "Density" and "Percentage".

        Raises:
            ValueError: if an unsupported metric is provided.
        """
        self.metric = metric
        if metric == "Density":
            self.values_carcinoma = df[COLUMN_DENSITY_CARCINOMA]
            self.values_stroma = df[COLUMN_DENSITY_STROMA]
        elif metric == "Percentage":
            self.values_carcinoma = df[COLUMN_RATIO_CARCINOMA]
            self.values_stroma = df[COLUMN_RATIO_STROMA]
        else:
            msg = f"Unsupported metric {metric}. Supported metrics are 'Density' and 'Percentage'."
            raise ValueError(msg)

        self.set_thresholds(carcinoma_thresh=carcinoma_thresh, stroma_thresh=stroma_thresh)

    def set_thresholds(self, *, carcinoma_thresh: float, stroma_thresh: float) -> None:
        """Set thresholds for tumor immune phenotypes.

        Args:
            carcinoma_thresh: The threshold for lymphocytes in carcinoma.
            stroma_thresh: The threshold for lymphocytes in stroma.
        """
        self.carc_thres = carcinoma_thresh
        self.strom_thres = stroma_thresh

        # invalidate cached classification
        self.__dict__.pop("phenotype_classification", None)

    @cached_property
    def phenotype_classification(self) -> np.ndarray:
        """Compute the tumor immune phenotype based on given thresholds.

        For each slide, computes the following:
        ```
        if lymphocyte fraction in carcinoma > carcinoma threshold:
            return inflamed
        elif lymphocyte fraction in stroma > stroma threshold:
            return excluded
        else:
            return desert
        ```

        Returns:
            The tumor immune phenotype in ["inflamed", "excluded", "desert"] for each slide.
        """
        status = np.where(self.values_carcinoma > self.carc_thres, "inflamed", "")
        status = np.where((self.values_stroma > self.strom_thres) & (~status.astype(bool)), "excluded", status)
        return np.where(~status.astype(bool), "desert", status)

    def plot_tip_classification(self) -> go.Figure:
        """Plot TIP classification of each slide.

        Plots each slide's lymphocyte density in carcinoma and stroma regions,
        highlighting inflamed, excluded and desert tumors with different colors.


        Returns:
            The rendered plot.
        """
        fig = go.Figure()
        fig.update_layout(
            xaxis={"title": {"text": f"Lymphocyte {self.metric.lower()} in carcinoma"}},
            yaxis={"title": {"text": f"Lymphocyte {self.metric.lower()} in stroma"}},
        )

        # plot thresholds as horizontal and vertical dashed lines
        fig.add_vline(
            x=self.carc_thres,
            line_dash="dash",
            showlegend=False,
        )

        fig.add_shape(
            type="line",
            x0=0,
            y0=self.strom_thres,
            x1=self.carc_thres,
            y1=self.strom_thres,
            line={"dash": "dash"},
        )

        # add desert highlighting
        fig.add_scatter(
            x=[0, self.carc_thres, self.carc_thres, 0],
            y=[0, 0, self.strom_thres, self.strom_thres],
            line_width=0,
            fillcolor=IDE_COLORS["desert"],
            opacity=0.2,
            fill="toself",
            mode="lines",
            showlegend=False,
        )

        # add excluded highlighting
        fig.add_scatter(
            x=[0, self.carc_thres, self.carc_thres, 0],
            y=[self.strom_thres, self.strom_thres, self.values_stroma.max(), self.values_stroma.max()],
            line_width=0,
            fillcolor=IDE_COLORS["excluded"],
            opacity=0.2,
            fill="toself",
            mode="lines",
            showlegend=False,
        )

        # add inflamed highlighting
        fig.add_scatter(
            x=[self.carc_thres, self.values_carcinoma.max(), self.values_carcinoma.max(), self.carc_thres],
            y=[0, 0, self.values_stroma.max(), self.values_stroma.max()],
            line_width=0,
            fillcolor=IDE_COLORS["inflamed"],
            opacity=0.2,
            fill="toself",
            mode="lines",
            showlegend=False,
        )

        # plot the data points last so that the hover tooltip is not blocked by the square filled areas that
        # would otherwise lie on top
        for ide_cls, color in IDE_COLORS.items():
            fig.add_scatter(
                x=self.values_carcinoma[self.phenotype_classification == ide_cls],
                y=self.values_stroma[self.phenotype_classification == ide_cls],
                mode="markers",
                name=ide_cls,
                marker={"color": color},
            )

        return fig

    def get_distribution_table(self) -> pd.DataFrame:
        """Get the distribution of tumor immune phenotypes.

        Returns:
            A dataframe with the percentage of samples in each tumor immune phenotype.
        """
        counts = pd.DataFrame(self.phenotype_classification).value_counts().reset_index()

        count_arr = np.asarray(counts["count"])
        counts["count"] = count_arr / count_arr.sum()
        return counts.sort_values(by=0).rename(columns={0: "Tumor immune phenotype"})
