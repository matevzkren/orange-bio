"""
==============================================================================
DictyMutants - An interface to Dictyostelium discoideum mutants from Dictybase
==============================================================================

:mod:`DictyMutants` is a python module for accessing Dictyostelium discoideum 
mutant collections from the `Dictybase <http://www.dictybase.org/>`_ website.

The mutants are presented as `DictyMutant` objects with their respective name,
strain descriptor, associated genes and associated phenotypes.

>>> from Orange.bio.obiDictyMutants import *
>>> # Create a set of all mutant objects
>>> dicty_mutants = mutants() 
>>> # List a set of all genes referenced by a single mutant
>>> print mutant_genes(dicty_mutants[0])
['cbfA']
>>> # List a set of all phenotypes referenced by a single mutant
>>> print mutant_phenotypes(dicty_mutants[0])
['aberrant protein localization']
>>> # List all genes or all phenotypes referenced on Dictybase
>>> print genes()
>>> print phenotypes()
>>> # Display a dictionary {phenotypes: set(mutant_objects)}
>>> print phenotype_mutants()
>>> # Display a dictionary {genes: set(mutant_objects)}
>>> print gene_mutants()
"""

import os
import urllib2
import shutil
import pickle

from collections import defaultdict

from Orange.orng import orngServerFiles

from Orange.utils.serverfiles import localpath_download

domain = "dictybase"
pickle_file = "mutants.pkl"
tags = ["Dictyostelium discoideum", "mutant", "dictyBase", "phenotype"]

class DictyMutant(object):
    """
    A class representing a single Dictyostelium discoideum mutant 
    from Dictybase
   
    :param mutant_entry: A single mutant entry from 
        dictybase's `all curated mutants file <http://dictybase.org/db/cgi-bin/dictyBase/download/download.pl?area=mutant_phenotypes&ID=all-mutants.txt>`_ (updated monthly)
    :type mutant_entry: str

    :ivar DictyMutant.name: dictyBase ID for a mutant
    :ivar DictyMutant.descriptor: dictyBase strain descriptor of a mutant
    :ivar DictyMutant.genes: all of the mutant's associated genes
    :ivar DictyMutant.phenotypes: all of the mutant's associated phenotypes

    """
    def __init__(self, mutant_entry):
        mutant = mutant_entry.split("\t")
        self.name = mutant[0]
        self.descriptor = mutant[1]
        self.genes = mutant[2].split(" | ")
        self.phenotypes = mutant[3].split(" | ")
        self.null = False
        self.overexp = False
        self.multiple = False
        self.develop = False
        self.other = False
 
class DictyMutants(object):
    """
    A class representing the collection of all Dictybase mutants as 
    a dictionary of `DictyMutant` objects
    
    :param local_database_path: A user defined path for storing dicty mutants objects in a file. If `None` then a default database path is used.
    
    """
    
    VERSION=1
    DEFAULT_DATABASE_PATH = orngServerFiles.localpath("DictyMutants") #use a default local folder for storing the genesets
    
    def __init__(self, local_database_path=None):
        self.local_database_path = local_database_path if local_database_path is not None else self.DEFAULT_DATABASE_PATH
        
        if not os.path.exists(self.local_database_path):
            os.mkdir(self.local_database_path)
            
        self._mutants = pickle.load(open(localpath_download(domain, pickle_file), "rb"))
              
    def update_file(self, name):
        url = "http://dictybase.org/db/cgi-bin/dictyBase/download/download.pl?area=mutant_phenotypes&ID="
        filename = os.path.join(self.local_database_path, name)
        temp_file = os.path.join(self.local_database_path, name + "_temp")
        stream = urllib2.urlopen(url + name)
    
        with open(temp_file, "wb") as file:
            shutil.copyfileobj(stream, file)
    
        os.rename(temp_file, filename)
        return filename
    
    def load_mutants(self, file):
        data = open(file)
        data_header = data.readline()
        data = data.read()
        return data.splitlines()
                 
    def download_mutants(self):   
        all_mutants = self.load_mutants(self.update_file("all-mutants.txt"))
        null_mutants = self.load_mutants(self.update_file("null-mutants.txt"))
        overexp_mutants = self.load_mutants(self.update_file("overexpression-mutants.txt"))
        multiple_mutants = self.load_mutants(self.update_file("multiple-mutants.txt"))
        develop_mutants = self.load_mutants(self.update_file("developmental-mutants.txt"))
        other_mutants = self.load_mutants(self.update_file("other-mutants.txt"))
   
        _mutants = [DictyMutant(mutant) for mutant in all_mutants]
        
        the_nulls = set([DictyMutant(line).name for line in null_mutants])
        the_overexps = set([DictyMutant(line).name for line in overexp_mutants])
        the_multiples = set([DictyMutant(line).name for line in multiple_mutants])
        the_develops = set([DictyMutant(line).name for line in develop_mutants])
        the_others = set([DictyMutant(line).name for line in other_mutants])

        for mutant in _mutants:
            if mutant.name in the_nulls: mutant.null = True
            if mutant.name in the_overexps: mutant.overexp = True 
            if mutant.name in the_multiples: mutant.multiple = True
            if mutant.name in the_develops: mutant.develop = True
            if mutant.name in the_others: mutant.other = True
       
        final_mutants = {x: x for x in _mutants}
        return final_mutants

    def pickle_data(self):
        return pickle.dumps(self.download_mutants(), -1)

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_shared_dict"):
            dicty = DictyMutants()
            cls._shared_dict = dicty.__dict__
        instance = DictyMutants.__new__(DictyMutants)
        instance.__dict__ = cls._shared_dict
        return instance

    def mutants(self):
        return self._mutants.keys()

    def genes(self):
        return sorted(set(reduce(list.__add__, [self.mutant_genes(mutant) for mutant in self.mutants()], [])))

    def phenotypes(self):
        return sorted(set(reduce(list.__add__, [self.mutant_phenotypes(mutant) for mutant in self.mutants()], [])))

    def mutant_genes(self, mutant):
        return self._mutants[mutant].genes
    
    def mutant_phenotypes(self, mutant):
        return self._mutants[mutant].phenotypes

    def gene_mutants(self):
        dgm = defaultdict(set)
        for mutant, genes in [(mutant, self.mutant_genes(mutant)) for mutant in self.mutants()]:
            for gene in genes:
                dgm[gene].add(mutant)
        return dgm

    def phenotype_mutants(self):
        dpm = defaultdict(set)
        for mutant, phenotypes in [(mutant, self.mutant_phenotypes(mutant)) for mutant in self.mutants()]:
            for phenotype in phenotypes:
                dpm[phenotype].add(mutant)
        return dpm

def mutants():
    """ Return all mutant objects
    """
    return DictyMutants.get_instance().mutants()

def genes():
    """ Return a set of all genes referenced in dictybase
    """
    return DictyMutants.get_instance().genes()

def phenotypes():
    """ Return a set of all phenotypes referenced in dictybase
    """
    return DictyMutants.get_instance().phenotypes()

def mutant_genes(mutant):
    """ Return a set of all genes referenced by a mutant in dictybase
    """
    return DictyMutants.get_instance().mutant_genes(mutant)

def mutant_phenotypes(mutant):   
    """ Return a set of all phenotypes referenced by a mutant in dictybase
    """
    return DictyMutants.get_instance().mutant_phenotypes(mutant)

def gene_mutants():
    """ Return a dictionary {gene: set(mutant_objects for mutant), ...}
    """
    return DictyMutants.get_instance().gene_mutants()

def phenotype_mutants():
    """ Return a dictionary {phenotype: set(mutant_objects for mutant), ...}
    """
    return DictyMutants.get_instance().phenotype_mutants()

def download_mutants():
    return DictyMutants.get_instance().pickle_data()

if  __name__  == "__main__":
    dicty_mutants = mutants()
    print mutant_phenotypes(dicty_mutants[0])
#    print(phenotypes())#_mutants())    
