"""Deterministic performance analysis; the LLM never decides classifications."""
import math
import pandas as pd

REQUIRED = {'brandname', 'revenue', 'Order', 'Boss Gmail'}

def assess_hotels(df: pd.DataFrame) -> list[dict]:
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f'Missing expected columns: {sorted(missing)}')
    frame = df.copy()
    frame['revenue'] = pd.to_numeric(frame['revenue'], errors='raise')
    frame['Order'] = pd.to_numeric(frame['Order'], errors='raise')
    if frame.empty:
        raise ValueError('No hotels in source data')
    if frame['brandname'].isna().any() or frame['brandname'].astype(str).str.strip().eq('').any():
        raise ValueError('Hotel name cannot be empty')
    if (frame['revenue'] < 0).any() or (frame['Order'] < 0).any():
        raise ValueError('Negative revenue or orders are not supported')
    if (frame['Order'] % 1 != 0).any():
        raise ValueError('Orders must be whole numbers')
    median_revenue = float(frame['revenue'].median())
    median_orders = float(frame['Order'].median())
    output = []
    for _, row in frame.iterrows():
        revenue, orders = float(row['revenue']), int(row['Order'])
        # Transparent benchmark: both revenue and order count >= peer median.
        good = revenue >= median_revenue and orders >= median_orders
        output.append({
            'hotel': str(row['brandname']).strip(),
            'owner_email': str(row['Boss Gmail']).strip(),
            'revenue': revenue, 'orders': orders,
            'aov': round(revenue / orders, 2) if orders else None,
            'median_revenue': median_revenue,
            'median_orders': median_orders,
            'classification': 'Doing Well' if good else 'Needs Improvement',
        })
    return output
