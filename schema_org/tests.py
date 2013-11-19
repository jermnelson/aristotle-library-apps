"""
 :mod:`tests` Tests Schema.org Models
"""
from models import *

from unittest import TestCase, main

class ModelGetClassesTest(TestCase):

    def setUp(self):
        self.schema_classes = get_classes()
        

    def test_food_related(self):
        self.assert_('FoodEstablishment' in self.schema_classes)
        self.assert_('Bakery' in self.schema_classes)
        self.assert_('BarOrPub' in self.schema_classes)
        self.assert_('Brewery' in self.schema_classes)
        self.assert_('CafeOrCoffeeShop' in self.schema_classes)
        self.assert_('FastFoodRestaurant' in self.schema_classes)
        self.assert_('IceCreamShop' in self.schema_classes)
        self.assert_('Restaurant' in self.schema_classes)
        self.assert_('Winery' in self.schema_classes)

    def tearDown(self):
        pass

class ModelAddPropertiesTest(TestCase):

    def setUp(self):
        self.schema_classes = add_properties(get_classes())

    def test_article(self):
        self.assertEquals(self.schema_classes['Article']['children'],
                          ['BlogPosting',
                           'NewsArticle',
                           'ScholarlyArticle'])
        # From Thing ancestor
        self.assert_(
            'url' in self.schema_classes['Article']['properties'])
        # From CreativeWork parent
        self.assert_(
            'headline' in self.schema_classes['Article']['properties'])
        # From self
        self.assert_(
            'articleBody' in self.schema_classes['Article']['properties'])
        

    def test_book(self):
        # From Thing ancestor
        self.assert_(
            'description' in self.schema_classes['Book']['properties'])
        # From CreativeWork parent
        self.assert_(
            'datePublished' in self.schema_classes['Book']['properties'])
        # From self
        self.assert_(
            'bookEdition' in self.schema_classes['Book']['properties'])                       
            
    def tearDown(self):
        pass

class BookTest(TestCase):

    def setUp(self):
        pass

    def test_docstring(self):
        self.assert_(Book.__doc__.startswith('Book - URL'))

    def test_properties(self):
        self.assert_(hasattr(Book, 'about'))
        self.assert_(hasattr(Book, 'aggregateRating'))
        self.assert_(hasattr(Book, 'audio'))
        self.assert_(hasattr(Book, 'author'))
        self.assert_(hasattr(Book, 'awards'))
        self.assert_(hasattr(Book, 'bookEdition'))
        self.assert_(hasattr(Book, 'bookFormat'))
        self.assert_(hasattr(Book, 'contentLocation'))
        self.assert_(hasattr(Book, 'contentRating'))
        self.assert_(hasattr(Book, 'datePublished'))
        self.assert_(hasattr(Book, 'description'))
        self.assert_(hasattr(Book, 'editor'))
        self.assert_(hasattr(Book, 'encodings'))
        self.assert_(hasattr(Book, 'genre'))
        self.assert_(hasattr(Book, 'headline'))
        self.assert_(hasattr(Book, 'illustrator'))
        self.assert_(hasattr(Book, 'image'))
        self.assert_(hasattr(Book, 'inLanguage'))
        self.assert_(hasattr(Book, 'interactionCount'))
        self.assert_(hasattr(Book, 'isFamilyFriendly'))
        self.assert_(hasattr(Book, 'isbn'))
        self.assert_(hasattr(Book, 'keywords'))
        self.assert_(hasattr(Book, 'name'))
        self.assert_(hasattr(Book, 'numberOfPages'))
        self.assert_(hasattr(Book, 'offers'))
        self.assert_(hasattr(Book, 'publisher'))
        self.assert_(hasattr(Book, 'reviews'))
        self.assert_(hasattr(Book, 'url'))
        self.assert_(hasattr(Book, 'video'))

    def tearDown(self):
        pass

    

class ThingTest(TestCase):

    def setUp(self):
        pass

    def test_docstring(self):
        self.assert_(Thing.__doc__.startswith("Thing - URL")),

    def test_properties(self):
        self.assert_(hasattr(Thing, 'description'))
        self.assert_(hasattr(Thing, 'image'))
        self.assert_(hasattr(Thing, 'name'))
        self.assert_(hasattr(Thing, 'url'))

    def test_null_properties(self):
        "An instance of Thing attributes should all be None"
        thing = Thing()
        self.assertEquals(thing.description,
                          None)
        self.assertEquals(thing.image,
                          None)
        self.assertEquals(thing.name,
                          None)
        self.assertEquals(thing.url,
                          None)

    def tearDown(self):
        pass


if __name__ == '__main__':
    main()
