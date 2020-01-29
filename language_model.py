'''
Language submodel

Collect all the code needed to generate random names for people, places, ships
'''

import string
import random
import json
from collections import defaultdict
import numpy as np

import tracery

from utils import weighted_random


class RandomLanguageModel:
    ''' A language model defined by a random syllable distribution
    '''
    
     # Tracery grammar for naming things:
    grammar = {
        "virtue": ["Courage", "Kindness", "Wisdom", "Cunning", "Charity", 
                   "Mercy", "Love", "Pride", "Glory"],
        "title": ["Prince", "Princess", "Duke", "President", "Exilarch", 
                  "Duchess", "Elector", "Senator"],
        "ship_name": ["#virtue# of #place#", "#place# #virtue#", 
                       "#title# of #place#", "#place# #title#", 
                       "#virtue# #virtue#", "#title#'s #virtue#"],
        "place": []
    }
    
    def __init__(self, n_prefixes=3):
        
        self.syllable_weights = {}
        self._make_weighted_syllables()
        
        # Place name parameters
        self.prob_prefix = 0.3 
        self.n_prefixes = n_prefixes
        self.place_name_prefixes = [
            weighted_random(self.syllable_weights).title() 
                    for _ in range(self.n_prefixes) ]
        self.place_name_syllables = {1: 1, 2: 3, 3: 3, 4: 1}
        
    
    def _make_weighted_syllables(self, zipf_param=3):
        ''' Create a dictionary of syllables with weights
        '''
        syllables = []
        vowels = "aeiouy"
        for a in vowels:
            for b in string.ascii_lowercase:
                syllables.append(a+b)
                syllables.append(b+a)

        self.syllable_weights = {k: np.random.zipf(3)
                                 for k in syllables}
    
    def make_word(self, syl_count=3, p_odd=0.5):
        ''' Make a random word
        '''
        word = "".join([weighted_random(self.syllable_weights) 
                        for i in range(syl_count)])
        if len(word) > 2 and random.random() < p_odd:
            word = word[:-1]
        return word.title()

    def make_place_name(self):
        name = ""
        if random.random() < self.prob_prefix:
            name += random.choice(self.place_name_prefixes).title() + " "
        syl_count = weighted_random(self.place_name_syllables)
        name += self.make_word(syl_count).title()
        return name
    
    def add_place_name(self, place_name):
        ''' Add a place-name to the Tracery grammar used for ship-naming
        
        Ensures that ships can be named after in-world cities
        '''
        self.grammar["place"].append(place_name)
    
    def make_ship_name(self):
        ''' Generate a random ship name
        '''
        grammar = tracery.Grammar(self.grammar)
        return grammar.flatten("#ship_name#")
    
class MarkovChain:
    ''' Train an n-order Markov chain and generate words from it.
    
    (The order is simply how many characters to use to choose the next one)
    Transitions are stored as a defaultdict with the structure 
        {token: [char, char, ...], token: ...}
    Special tokens "<START>" and "<END>" designate the beginning and end of
    a string.
        
    '''
    
    def __init__(self, order=1, vocabulary=None):
        self.transitions = defaultdict(list)
        self.order = order
        if vocabulary is not None:
            self.train(vocabulary)
    
    def train(self, vocabulary, replace=False):
        if replace:
            self.transitions = defaultdict(list)
        for word in vocabulary:
            self.transitions["<START>"].append(word[:self.order])
            for i in range(self.order, len(word)):
                self.transitions[word[i-self.order:i]].append(word[i])
            self.transitions[word[-self.order:]].append("<END>")
    
    def generate(self):
        word = ""
        token = "<START>"
        while True:
            next_char = random.choice(self.transitions[token])
            if next_char == "<END>":
                return word
            word += next_char
            token = word[-self.order:]
        return word

class MarkovLanguage:
    ''' Use Markov Chain models to generate names and places.
    '''
    
    def __init__(self, name_corpus, place_corpus, order=2):
        ''' Create a new language model
        
        Args:
            name_corpus: List of words to use as (first) names
            place_corpus: List of words to use for place-names
        '''
        self.order = order
        self.name_model = MarkovChain(order, name_corpus)
        self.place_model = MarkovChain(order, place_corpus)
    
    def make_place_name(self):
        return self.place_model.generate()
    
    def make_ship_name(self):
        if random.random() < 0.5:
            return "The " + self.name_model.generate()
        else:
            return "The " + self.make_place_name()
    
    def add_place_name(self, place_name):
        ''' TODO: populate this
        '''
        pass
    
    @classmethod
    def make_psuedo_english(cls, order=2):
        ''' Make Markov chain of English names from hard-coded corpora
        '''
        
        with open("corpora/english_towns_cities.json") as f:
            place_corpus = json.load(f)
            town_names = place_corpus["towns"] + place_corpus["cities"]
        
        with open("corpora/firstNames.json") as f:
            name_corpus = json.load(f)
            first_names = name_corpus["firstNames"]
        
        return cls(first_names, town_names, order)
        