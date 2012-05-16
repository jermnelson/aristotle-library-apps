Feature: Portfolio App Navigation Action Bar Default Display
    In order to display the default app view for the Navigation Action Bar
    As users
    the Portfolio App displays a Navigation Action Bar

    Scenario: Display Portfolio App Navigation Action Bar
        Given I access the Portfolio App with a nav-action-bar
        Then I see Portfolio App Navigation Action Bar

    Scenario: Display Portfolio App Navigation Action Bar Icon
        Given I access the Portfolio App with a nav-action-bar
        Then I see the icon in the Navigation Action Bar

    Scenario: Display Portfolio App Navigation Action Bar Title
        Given I access the Portfolio App with a nav-action-bar
        Then I see the title in the Navigation Action Bar is App Portfolio

    Scenario: Display Institution Logo in the Navigation Action Bar
        Given I access the Portfolio App with a nav-action-bar
        Then I see the logo in the Navigation Action Bar




    



