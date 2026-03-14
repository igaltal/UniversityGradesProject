"""
University Grades - Automated grade monitoring for Reichman University.

Layered architecture:
- core: Config, GradeRepository, Notifier (domain/infrastructure)
- scraping: Selenium scraper for university portal
- web: Flask application (login, dashboard, scraper trigger)
"""

__version__ = "1.0.0"
