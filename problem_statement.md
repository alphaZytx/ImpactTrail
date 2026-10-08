# Problem Statement

The objective of this case study is to design and implement a platform capable of ingesting and analyzing real-time, unstructured data to generate actionable financial risk signals.

The primary deliverable is a unified AI/NLP Risk Engine. This engine will serve as the central processing unit, responsible for parsing text-based data from sources such as news feeds and social media, and converting it into structured output.

Upon completion of the core engine, teams are required to implement at least one of the following downstream modules to demonstrate a practical application of the generated risk intelligence:

- **Module A:** A tactical, high-frequency stock index rebalancer.
- **Module B:** A strategic, event-driven portfolio stress-testing tool.

The project is structured modularly to allow for focused development on distinct components within the specified timeframe.

## 2. The Core Challenge: The AI/NLP Risk Engine

Your primary task is to build a robust data pipeline and NLP model that can ingest text from various sources and output structured, machine-readable risk signals.

Engine Requirements:

- **Data Ingestion:** The engine must be able to process text from at least two different sources (e.g., financial news articles and Twitter/X posts).
- **NLP-Driven Analysis:** The engine must analyze the text and, for a given company or event, output structured data with the following fields:
- **Sentiment Score:** A numerical score indicating positive, negative, or neutral sentiment (e.g., from -1.0 to 1.0).
- **Event Classification:** A categorical label for the type of event discussed (e.g., Geopolitical, Macroeconomic, Credit Event, Merger/Acquisition, Product Launch).
- **Impact Score:** A predicted severity score (e.g., 1-10) indicating the potential market impact of the event.
- **Output:** The engine should make these structured signals available for consumption by downstream applications, for example, through a simple API or by writing to a file.

## 3. Downstream Applications (Choose at least ONE)

Once your AI/NLP Risk Engine is operational, you must build at least one of the following modules to demonstrate its capabilities.

### Module A: Tactical Index Rebalancing

**Objective:** Create a system that dynamically rebalances a mock stock index (e.g., a selection of 10-20 stocks from the S&P 100) based on real-time sentiment.

**Functionality:**

- This module will subscribe to the Sentiment Score from your NLP Risk Engine.
- For each stock in your mock index, the system will adjust the stock's weight in the portfolio.
- **Positive Sentiment:** Increase the weight of the stock.
- **Negative Sentiment:** Decrease the weight of the stock.
- **Visualization:** Create a simple dashboard that visualizes the changing weights of the stocks in your index over time.

### Module B: Strategic Portfolio Stress Testing

**Objective:** Design a conceptual tool that simulates the impact of major real-world events on a synthetic portfolio of wholesale banking assets.

**Functionality:**

- This module will subscribe to the Event Classification and Impact Score from your NLP Risk Engine.
- Define a synthetic portfolio using the provided sample transaction data. The portfolio should include a mix of asset types (e.g., loans, bonds, derivatives).
- When a high-impact event is detected (e.g., Geopolitical with an Impact Score > 7), the module will trigger a "stress test."
- **Stress Test Simulation:** For the purpose of the hackathon, the stress test can be a simplified model. For example, you can define a set of shocks (e.g., a 10% drop in all equity prices, a 2% increase in interest rates) that are applied to your portfolio when a specific event type is detected.
- **Visualization:** Create a dashboard that shows the portfolio's value before and after the stress test, highlighting the impact of the simulated event.

## 4. Open-Source Datasets and Resources

To ensure this case study is implementable, here are several free, open-source datasets and APIs that you can use. You are encouraged to use these as a starting point and augment them with other sources you find. All listed resources have free tiers and do not require payment.

### Unstructured Data for NLP (News & Social Media)

| Resource | Description | Use Case |
|---|---|---|
| The GDELT Project | A massive, open database that monitors global news media in over 100 languages, updated every 15 minutes. It categorizes events and themes, making it perfect for the NLP Risk Engine. | Ingesting a real-time, categorized feed of global events to power the Event Classification and Impact Score in your NLP engine. |
| Financial News Sentiment Datasets (Kaggle) | Kaggle hosts numerous datasets with financial news headlines and articles, often pre-labeled with sentiment. A popular example is the "Sentiment Analysis for Financial News" dataset. | Training or fine-tuning your Sentiment Score model. Can also be used for back-testing your strategies. |
| News API (newsapi.org) | Provides a free developer plan to fetch recent news articles from thousands of sources. It's great for getting real-time headlines and articles for your demo. | A live source of news for your NLP engine. |
| Historical Stock Tweets (Kaggle) | Datasets like "Tweet Sentiment's Impact on Stock Returns" contain millions of tweets related to specific stocks, often with sentiment polarity scores. | A rich source for training your sentiment model and understanding the relationship between social media and stock returns. |

### Financial Data (Transactions & Market Prices)

| Resource | Description | Use Case |
|---|---|---|
| yfinance Python Library | An extremely popular and easy-to-use library to download historical market data for stocks, indices, and currencies directly from Yahoo Finance. | Fetching historical price data for Module A (Index Rebalancing) and Module B (Stress Testing). |
| Alpha Vantage | Offers a free API for real-time and historical data on stocks, forex, and cryptocurrencies, including technical indicators. | An alternative or supplement to yfinance for fetching market data. |
| Salad Money Open Banking Transaction Data | A secure dataset containing anonymized transaction-level data from UK key workers. It includes spending categories, amounts, and demographic information. | An excellent source for creating a realistic synthetic portfolio for Module B, with varied transaction types and user profiles. |
| Financial Transactions Dataset (Kaggle) | This dataset combines transaction records, customer information, and card data, designed for fraud detection and customer behavior analysis. | Another great option for building the synthetic portfolio in Module B, providing a rich set of features for analysis. |

## Required Deliverables

The following items must be submitted for evaluation:

1. **Source Code:** A link to a public source code repository (e.g., GitHub) containing the complete implementation.
2. **Live Demonstration:** A functional, live demonstration of the application, not to exceed 5 minutes.
3. **Presentation Materials:** A brief presentation (maximum 7 slides) summarizing the project architecture, challenges, and results.

**Please refer the mentioned link for Case Study Submission Guidelines**

**Link:[https://docs.google.com/document/d/1ktSFX](https://docs.google.com/document/d/1ktSFXSiOFfQSuhMhbH2GEF6sAtUzHy6N/edit)**
