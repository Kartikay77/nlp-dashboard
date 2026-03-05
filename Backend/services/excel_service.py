import os
import uuid
import pandas as pd


def _safe_results_df(results: dict, key: str, columns=None) -> pd.DataFrame:
    df = results.get(key)
    if isinstance(df, pd.DataFrame):
        return df
    return pd.DataFrame(columns=columns or [])


def _excel_range(sheet_name: str, col_letter: str, n_rows: int) -> str:
    """
    Builds an Excel range string from row 2 to row (n_rows + 1).
    Ensures at least one data row range so charts don't break.
    """
    end_row = max(2, n_rows + 1)
    return f"={sheet_name}!${col_letter}$2:${col_letter}${end_row}"


def _set_basic_sheet_formatting(writer, sheet_name: str, df: pd.DataFrame):
    ws = writer.sheets.get(sheet_name)
    if ws is None:
        return

    # Freeze header row
    ws.freeze_panes(1, 0)

    # Set simple column widths based on column name lengths and sample data
    if df is None or df.empty:
        for idx, col in enumerate(df.columns if df is not None else []):
            width = min(max(len(str(col)) + 2, 12), 40)
            ws.set_column(idx, idx, width)
        return

    for idx, col in enumerate(df.columns):
        try:
            max_data_len = int(df[col].astype(str).str.slice(0, 200).map(len).max())
        except Exception:
            max_data_len = 12
        width = min(max(len(str(col)) + 2, max_data_len + 2, 12), 60)
        ws.set_column(idx, idx, width)


def build_excel_dashboard(raw_df, filtered_df, results: dict, output_dir="exports"):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"nlp_dashboard_{uuid.uuid4().hex[:8]}.xlsx")

    # Safely pull expected result dataframes
    top_words_df = _safe_results_df(results, "top_words_df", ["word", "count"])
    top_phrases_df = _safe_results_df(results, "top_phrases_df", ["phrase", "count"])
    clustered_df = _safe_results_df(results, "clustered_df")
    phrase_groups_df = _safe_results_df(results, "phrase_groups_df")
    cluster_counts_df = _safe_results_df(results, "cluster_counts_df", ["cluster", "count"])

    # Source counts
    if isinstance(filtered_df, pd.DataFrame) and not filtered_df.empty and "source" in filtered_df.columns:
        src_counts_df = filtered_df.groupby("source").size().reset_index(name="count")
    else:
        src_counts_df = pd.DataFrame(columns=["source", "count"])

    # Trend (handles either datetime or message_datetime)
    if isinstance(filtered_df, pd.DataFrame) and not filtered_df.empty:
        temp = filtered_df.copy()
        dt_col = None
        if "datetime" in temp.columns:
            dt_col = "datetime"
        elif "message_datetime" in temp.columns:
            dt_col = "message_datetime"

        if dt_col:
            temp["date"] = pd.to_datetime(temp[dt_col], errors="coerce").dt.date
            trend_df = (
                temp.dropna(subset=["date"])
                .groupby("date")
                .size()
                .reset_index(name="count")
                .sort_values("date")
            )
        else:
            trend_df = pd.DataFrame(columns=["date", "count"])
    else:
        trend_df = pd.DataFrame(columns=["date", "count"])

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        # Write sheets
        raw_df.to_excel(writer, sheet_name="Raw_Data", index=False)
        filtered_df.to_excel(writer, sheet_name="Filtered", index=False)
        top_words_df.to_excel(writer, sheet_name="Top_Words", index=False)
        top_phrases_df.to_excel(writer, sheet_name="Top_Phrases", index=False)
        clustered_df.to_excel(writer, sheet_name="Clusters", index=False)
        phrase_groups_df.to_excel(writer, sheet_name="Phrase_Groups", index=False)
        src_counts_df.to_excel(writer, sheet_name="Source_Counts", index=False)
        cluster_counts_df.to_excel(writer, sheet_name="Cluster_Counts", index=False)
        trend_df.to_excel(writer, sheet_name="Trend", index=False)

        # Format data sheets
        _set_basic_sheet_formatting(writer, "Raw_Data", raw_df)
        _set_basic_sheet_formatting(writer, "Filtered", filtered_df)
        _set_basic_sheet_formatting(writer, "Top_Words", top_words_df)
        _set_basic_sheet_formatting(writer, "Top_Phrases", top_phrases_df)
        _set_basic_sheet_formatting(writer, "Clusters", clustered_df)
        _set_basic_sheet_formatting(writer, "Phrase_Groups", phrase_groups_df)
        _set_basic_sheet_formatting(writer, "Source_Counts", src_counts_df)
        _set_basic_sheet_formatting(writer, "Cluster_Counts", cluster_counts_df)
        _set_basic_sheet_formatting(writer, "Trend", trend_df)

        workbook = writer.book
        dashboard = workbook.add_worksheet("Dashboard")

        # Dashboard title / summary
        title_fmt = workbook.add_format({"bold": True, "font_size": 14})
        label_fmt = workbook.add_format({"bold": True})
        dashboard.write("B1", "NLP Dashboard Summary", title_fmt)
        dashboard.write("R2", "Raw Rows", label_fmt)
        dashboard.write("S2", len(raw_df) if isinstance(raw_df, pd.DataFrame) else 0)
        dashboard.write("R3", "Filtered Rows", label_fmt)
        dashboard.write("S3", len(filtered_df) if isinstance(filtered_df, pd.DataFrame) else 0)
        dashboard.write("R4", "Sources", label_fmt)
        dashboard.write("S4", len(src_counts_df))
        dashboard.write("R5", "Clusters", label_fmt)
        dashboard.write("S5", len(cluster_counts_df))

        # Dynamic row counts for chart ranges
        n_top_words = len(top_words_df)
        n_top_phrases = len(top_phrases_df)
        n_src_counts = len(src_counts_df)
        n_cluster_counts = len(cluster_counts_df)
        n_trend = len(trend_df)

        # Top words chart
        c1 = workbook.add_chart({"type": "column"})
        c1.add_series({
            "name": "Top Words",
            "categories": _excel_range("Top_Words", "A", n_top_words),
            "values": _excel_range("Top_Words", "B", n_top_words),
        })
        c1.set_title({"name": "Top Words"})
        c1.set_x_axis({"name": "Word"})
        c1.set_y_axis({"name": "Count"})
        c1.set_legend({"none": True})
        dashboard.insert_chart("B3", c1, {"x_scale": 1.15, "y_scale": 1.1})

        # Top phrases chart
        c2 = workbook.add_chart({"type": "bar"})
        c2.add_series({
            "name": "Top Phrases",
            "categories": _excel_range("Top_Phrases", "A", n_top_phrases),
            "values": _excel_range("Top_Phrases", "B", n_top_phrases),
        })
        c2.set_title({"name": "Top Phrases"})
        c2.set_x_axis({"name": "Count"})
        c2.set_y_axis({"name": "Phrase"})
        c2.set_legend({"none": True})
        dashboard.insert_chart("B23", c2, {"x_scale": 1.15, "y_scale": 1.1})

        # Source distribution chart
        c3 = workbook.add_chart({"type": "pie"})
        c3.add_series({
            "name": "Source Distribution",
            "categories": _excel_range("Source_Counts", "A", n_src_counts),
            "values": _excel_range("Source_Counts", "B", n_src_counts),
            "data_labels": {"percentage": True},
        })
        c3.set_title({"name": "Filtered by Source"})
        dashboard.insert_chart("J3", c3, {"x_scale": 1.1, "y_scale": 1.0})

        # Cluster sizes chart
        c4 = workbook.add_chart({"type": "column"})
        c4.add_series({
            "name": "Cluster Sizes",
            "categories": _excel_range("Cluster_Counts", "A", n_cluster_counts),
            "values": _excel_range("Cluster_Counts", "B", n_cluster_counts),
        })
        c4.set_title({"name": "Message Clusters"})
        c4.set_x_axis({"name": "Cluster"})
        c4.set_y_axis({"name": "Count"})
        c4.set_legend({"none": True})
        dashboard.insert_chart("J23", c4, {"x_scale": 1.1, "y_scale": 1.1})

        # Trend chart
        c5 = workbook.add_chart({"type": "line"})
        c5.add_series({
            "name": "Message Trend",
            "categories": _excel_range("Trend", "A", n_trend),
            "values": _excel_range("Trend", "B", n_trend),
        })
        c5.set_title({"name": "Message Volume Trend"})
        c5.set_x_axis({"name": "Date"})
        c5.set_y_axis({"name": "Count"})
        c5.set_legend({"none": True})
        dashboard.insert_chart("B43", c5, {"x_scale": 1.35, "y_scale": 1.15})

        # Basic dashboard column widths
        dashboard.set_column("A:A", 2)
        dashboard.set_column("B:Q", 14)
        dashboard.set_column("R:R", 16)
        dashboard.set_column("S:S", 12)

    return file_path