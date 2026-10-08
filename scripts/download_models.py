from __future__ import annotations

from riskpulse.nlp.sentiment import FinBertSentimentAnalyzer


def main() -> None:
    analyzer = FinBertSentimentAnalyzer(allow_downloads=True)
    result = analyzer.analyze("The company reported strong profit growth.")
    print(f"Prepared {analyzer.backend}; smoke-test label={result.label.value}")


if __name__ == "__main__":
    main()
