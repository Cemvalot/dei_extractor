#!/usr/bin/env python3
"""
ID helper functions for DEI Extractor.

This module provides utility functions for processing and grouping IDs.
"""

import pandas as pd


def compute_arparchi_group_id(series: pd.Series) -> pd.Series:
    """
    Επιστρέφει dense rank (1..N) ανά μοναδικό ΑρΠαροχής.
    Προσπαθεί με αυξανόμενη αριθμητική ταξινόμηση. Αν υπάρχουν μη-αριθμητικά,
    κάνει fallback σε σειρά εμφάνισης (factorize).
    """
    s = series.astype(str).str.strip()
    s_num = pd.to_numeric(s.str.replace(r"\D", "", regex=True), errors="coerce")
    if s_num.isna().any():
        # order-of-appearance fallback (stable)
        return pd.Series(pd.factorize(s, sort=False)[0] + 1, index=series.index)
    # dense rank by ascending numeric value
    return s_num.rank(method="dense").astype(int)
