'''
Language submodel

Collect all the code needed to generate random names for people, places, ships
'''
import string
import random
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
    
    