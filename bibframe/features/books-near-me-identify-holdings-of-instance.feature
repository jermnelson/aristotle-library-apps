Feature: Books near me (Identify holdings of Instance)
    Alex is writing a book report on the "Phantom Tollbooth". Unfortunately,
    his copy has been inadvertently left on the bus never to be seen again and 
    the report is due tomorrow. In a attempt to solve this "problem", Alex's 
    mom is looking for a copy of this book held by a nearby library.

    Scenario: Query Pattern
        Given Alex's Mom location and her iPad application "Books Near Me"
        When Alex's Mom enters a title "Phantom Tollbooth"
        Then The iPad application creates a Query Pattern

    Scenario: Sample Response
        Given A query pattern for locating "Phantom Tollbooth"
        When A BIBFRAME response is generated
        Then Two libraries are located with BIBFRAME Work and Instance of "Phantom Tollbooth"
