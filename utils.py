import string
import random
import numpy as np


def weighted_random(choices):
    ''' Choose a dictionary key randomly with values as weights.
    '''
    total = sum([v for v in choices.values()])
    target = random.random() * total
    counter = 0
    for k, v in choices.items():
        if counter + v >= target:
            return k
        counter += v
    else:
        raise Exception("Shouldn't be here")

def make_weighted_syllables(zipf_param=3):
    ''' Create a dictionary of syllables with weights
    '''
    syllables = []
    vowels = "aeiouy"
    for a in vowels:
        for b in string.ascii_lowercase:
            syllables.append(a+b)
            syllables.append(b+a)

    syllable_weights = {k: np.random.zipf(3)
                        for k in syllables}
    return syllable_weights

def make_word(syllable_weights, syl_count=3, p_odd=0.5):
    ''' Make a random word from a weighted syllable dictionary
    '''
    word = "".join([weighted_random(syllable_weights) 
                    for i in range(syl_count)])
    if len(word) > 2 and random.random() < p_odd:
        word = word[:-1]
    return word.title()

def make_place_name_model(syllable_weights, n_prefixes, prob_prefix, 
                          syllable_count_weights):
    ''' Closure for making a consistent place-name generator.
    
    Place names might start with some prefixes, which are assumed to be one
    syllable long. 
    '''
    prefixes = [weighted_random(syllable_weights).title() 
                for _ in range(n_prefixes)]
    
    def make_place_name():
        name = ""
        if random.random() < prob_prefix:
            name += random.choice(prefixes).title() + " "
        syl_count = weighted_random(syllable_count_weights)
        name += make_word(syllable_weights, syl_count).title()
        return name
    
    return make_place_name
        
