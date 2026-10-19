"""DeepSeek creates wording only. Numeric evidence is validated by template fallback."""
import os


def fallback(h: dict, period: str) -> str:
    aov = f"{h['aov']:,.2f}" if h['aov'] is not None else 'N/A (no orders)'
    improvement = ('Keep monitoring booking volume and consider testing an upsell offer.'
                   if h['classification'] == 'Doing Well' else
                   'Review distribution visibility and test an offer to improve booking volume.')
    return (f"Hello,\n\nHere is the hotel performance summary for {period}.\n"
            f"Hotel: {h['hotel']}\nRevenue: {h['revenue']:,.2f} (currency not specified)\n"
            f"Orders: {h['orders']}\nAverage revenue per order: {aov}\n"
            f"Classification: {h['classification']} (relative to hotels in the supplied snapshot).\n"
            f"Recommendation: {improvement}\n\nRegards,\nHotel Partnerships Team")


def create_message(h: dict, period: str) -> tuple[str, str]:
    """Return body and origin. Falls back for no API key, failure, or suspicious output."""
    fallback_body = fallback(h, period)
    api_key = os.getenv('DEEPSEEK_API_KEY', '').strip()
    if not api_key:
        return fallback_body, 'TEMPLATE_NO_API_KEY'
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'))
        result = client.chat.completions.create(
            model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
            temperature=0.2,
            max_tokens=500,
            messages=[
                {'role': 'system', 'content': (
                    'You write clear, concise hotel-owner business emails. '\
                    'Never fabricate data, targets, currency, week-over-week comparisons or causes. '\
                    'Do not change the classification. Do not include a subject line. '\
                    'Use exactly the provided evidence and provide one actionable suggestion. '\
                    'State this is a comparison with the supplied hotel snapshot, not a growth rate.')},
                {'role': 'user', 'content': (
                    f"Period: {period}; hotel: {h['hotel']}; revenue: {h['revenue']:,.2f} "
                    f"(currency unspecified); orders: {h['orders']}; "
                    f"average revenue per order: {h['aov']}; "
                    f"classification: {h['classification']}; "
                    f"median revenue: {h['median_revenue']:,.2f}; "
                    f"median orders: {h['median_orders']}. "
                    'Write a short email addressed to the owner.')}
            ], timeout=25,
        )
        body = (result.choices[0].message.content or '').strip()
        # Simple guardrail, not a complete verification system.
        must_contain = [h['classification'], str(h['orders']), f"{h['revenue']:,.2f}"]
        if len(body) < 50 or not all(x in body for x in must_contain):
            return fallback_body, 'TEMPLATE_VALIDATION_FALLBACK'
        return body, 'DEEPSEEK'
    except Exception as exc:
        print(f'DeepSeek unavailable; using deterministic template ({type(exc).__name__}).')
        return fallback_body, 'TEMPLATE_API_FALLBACK'
