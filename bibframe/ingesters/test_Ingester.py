__author__ = "Jeremy Nelson"
from aristotle.settings import PROJECT_HOME
from bibframe.ingesters.Ingester import personal_name_parser
from unittest import TestCase

class TestPersonalNameParser(TestCase):

    def setUp(self):
        pass

    def test_standard_name_string(self):
        person = personal_name_parser('Austen, Jane, 1775-1817')
        self.assertEquals(person.get('schema:familyName'),
                          'Austen')
        self.assertEquals(person.get('schema:givenName'),
                          'Jane')
        self.assertEquals(person.get('rda:dateOfBirth'),
                          '1775')
        self.assertEquals(person.get('rda:dateOfDeath'),
                          '1817')

    def test_simple_name(self):
        person = personal_name_parser('Aristotle')
        self.assertEquals(person.get('schema:familyName'),
                          'Aristotle')

    def test_long_name(self):
        person = personal_name_parser('Williams III, Dr Robert John, 1934-2002')
        self.assertEquals(person.get('schema:familyName'),
                          'Williams')
        self.assertEquals(person.get('schema:givenName'),
                          'Robert')
        self.assertEquals(person.get('schema:additionalName'),
                          'John')
        self.assertEquals(person.get('schema:honorificPrefix'),
                          'Dr')
        self.assertEquals(person.get('schema:additionalName'),
                          'John')
        self.assertEquals(person.get('schema:honorificSuffix'),
                          'III')
        self.assertEquals(person.get('rda:dateOfBirth'),
                          '1934')
        self.assertEquals(person.get('rda:dateOfDeath'),
                          '2002')

    def test_living_author(self):
        person = personal_name_parser('Stephenson, Neal, 1958-')
        self.assertEquals(person.get('schema:familyName'),
                          'Stephenson')
        self.assertEquals(person.get('schema:givenName'),
                          'Neal')
        self.assertEquals(person.get('rda:dateOfBirth'),
                          '1958')
         

    def tearDown(self):
        pass
