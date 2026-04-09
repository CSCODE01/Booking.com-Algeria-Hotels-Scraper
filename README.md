# Booking.com Algeria Hotels Scraper 🏨🇩🇿

An advanced web scraping tool designed to extract detailed hotel information from Booking.com for major Algerian cities. This project is built using Python and Playwright, optimized for creating datasets for Machine Learning tasks.

## 📊 Extracted Data Points
- Hotel Name
- Price (DZD)
- User Rating (out of 10)
- Review Count
- Geographic Coordinates (Latitude/Longitude)
- Hotel Facilities (WiFi, Pool, Gym, etc.)
- Direct URL

## 🛠️ Technologies Used
- **Python**: Core programming language.
- **Playwright**: For browser automation and dynamic content rendering.
- **Playwright-Stealth**: To bypass anti-bot detection systems.
- **Pandas**: For data cleaning and CSV exportation.
- **Regex**: For precise extraction of hidden coordinates in the page source.

## 🚀 How to Run
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install playwright playwright-stealth pandas
