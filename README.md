**ScoritoOdds**
===============

A web application that scrapes and displays betting odds for football and tennis matches. The project leverages modern web scraping techniques with Playwright and presents the data in a user-friendly web interface built with Flask.

* * * * *

**Table of Contents**
---------------------

1.  [Features](#features)
2.  [Technologies Used](#technologies-used)
3.  [Installation](#installation)
4.  [Usage](#usage)
5.  [Screenshots](#screenshots)
6.  [Future Enhancements](#future-enhancements)
7.  [Contributing](#contributing)
8.  [License](#license)

* * * * *

**Features**
------------

-   **Football Odds**:
    -   Scrape odds for leagues like Eredivisie and Premier League.
    -   Highlight the team with the lowest odds in the UI.
-   **Tennis Odds**:
    -   Scrape odds for ATP tournaments, including player matchups.
    -   Display match date and time.
-   **Dropdown for League Selection**:
    -   Dynamically select leagues for both football and tennis.
-   **Responsive UI**:
    -   Built with Flask templates and styled for readability.
-   **Scalable Architecture**:
    -   Organized codebase with modular fetcher functions for different sports.

* * * * *

**Technologies Used**
---------------------

-   **Backend**: Python, Flask
-   **Web Scraping**: Playwright
-   **Frontend**: HTML, CSS (Bootstrap or custom styles)
-   **Database**: (Optional, future implementation)
-   **Version Control**: Git

* * * * *

**Installation**
----------------

1.  **Clone the Repository**:

    bash

    Copy code

    `git clone https://github.com/your-username/ScoritoOdds.git
    cd ScoritoOdds`

2.  **Set Up a Virtual Environment**:

    bash

    Copy code

    `python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate`

3.  **Install Dependencies**:

    bash

    Copy code

    `pip install -r requirements.txt`

4.  **Install Playwright and Browsers**:

    bash

    Copy code

    `playwright install`

5.  **Run the Application**:

    bash

    Copy code

    `python run.py`

6.  **Access the Web Application**: Open your browser and navigate to:

    arduino

    Copy code

    `http://127.0.0.1:5000/`

* * * * *

**Usage**
---------

-   Visit `/football` to view football odds.
-   Visit `/tennis` to view tennis odds.
-   Use the dropdown menus to switch between leagues.
-   Odds are highlighted to indicate the team/player with the lowest odds for quick insights.

* * * * *

**Screenshots**
---------------

### **Homepage**

### **Football Odds**

### **Tennis Odds**

* * * * *

**Future Enhancements**
-----------------------

-   Add more leagues and sports (e.g., darts, formula1).
-   impelent payment gateway
-   Implement a database to store historical odds.
-   Add user authentication for personalized features.
-   Provide API access for programmatic consumption of odds.
-   Improve UI with dynamic charts and data visualizations.

* * * * *

**Contributing**
----------------

Contributions are welcome! To get started:

1.  Fork this repository.
2.  Create a feature branch:

    bash

    Copy code

    `git checkout -b feature-name`

3.  Commit your changes:

    bash

    Copy code

    `git commit -m "Add your message"`

4.  Push to your fork:

    bash

    Copy code

    `git push origin feature-name`

5.  Create a Pull Request.

* * * * *

**License**
-----------

This project is licensed under the MIT License.

* * * * *

**Contact**
-----------

For questions or support, feel free to reach out:

-   **Author**: Jan Sparnaaij
-   **Email**: info@jandedataman.nl
-   **GitHub**: <https://github.com/JanSparnaaij>
