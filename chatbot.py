import re
from collections import Counter
import string
from string import punctuation
from math import sqrt
import hashlib
import sys
import logging


weight = 0 

import utils
conf = utils.get_config()


ACCURACY_THRESHOLD = 0.5
NO_DATA = "Sorry! I don't know what to say"

toBool = lambda str :  True if str=='True' else False

DEBUG_ASSOC = toBool(conf["DEBUG"]["assoc"])
DEBUG_WEIGHT = toBool(conf["DEBUG"]["weight"])
DEBUG_ITEMID = toBool(conf["DEBUG"]["itemid"])
DEBUG_MATCH = toBool(conf["DEBUG"]["match"])

def hashtext(stringText):
    """
    Return a string with first 16 numeric chars from hashing a given string
    
    Args: 
    stringText: String to be hashed

    Returns:
    16 hexadecimal digits

    Example 1
    Input: Hello
    Output: 8b1a9953c4611296

    Example 2
    Input: Hello how are you?
    Output: 1961b669810cb300
    """
    
    #hashlib md5 returns same hash for given string each time but might assign same hash to different sentences
    # the output of md5 is 128 bits or 32 hexadecimal digits but we are using only the first 16 bits for our case
    
    hashed = hashlib.md5(str(stringText).encode("utf-8")).hexdigest()
    return hashed[:16]

def item_id(entityName, text, cursor):
    """
    Retrieve an entity's unique ID from the database, given its associated text.
    If the row is not already present, it is inserted.
    The entity can either be a sentence or a word.

    Args:
    entityName: Entity that we are dealing with. Typically "word" or "sentence"
    text: The text associated with that entity. A string containing a single word or sentence
    cursor: pymysql cursor object

    Returns:
    hashid for the given text
    """

    tableName = entityName + 's'
    columnName = entityName

    # check whether 16-char hash of this text already exists
    hashid = hashtext(text)

    SQL_SELECT = f"SELECT hashid FROM {tableName} WHERE hashid = %s"
    if (DEBUG_ITEMID): 
        print(f"DEBUG ITEMID: {SQL_SELECT}")
    cursor.execute(SQL_SELECT, (hashid,))

    row = cursor.fetchone()

    if row:
        if (DEBUG_ITEMID): 
            print(f"DEBUG ITEMID: item found, just return hashid: {row["hashid"]} for {text}")
        return row['hashid']
    
    else:
        if (DEBUG_ITEMID): 
            print(f"DEUBG ITEMID: no item found, insert new hashid into {tableName} hashid: {hashid} text {text}")

        used = 0
        SQL_INSERT = f"INSERT INTO {tableName} (hashid, {columnName}) VALUES (%s, %s)"
        cursor.execute(SQL_INSERT, (hashid, text))
        return hashid

def get_words(text):
    """
    Retrieve the words present in a given string of text.
    The return value is a list of tuples where the first member is a lowercase word,
    and the second member the number of time it is present in the text.  
   
    Example:
      IN:  "Did the cow jump over the moon?"
      OUT: dict_items([('cow', 1), ('jump', 1), ('moon', 1), ('over', 1), ('the', 2), ('did', 1)])
    
    """
    puncRegexp = re.compile("[%s]" % re.escape(string.punctuation))
    text = puncRegexp.sub("",text)

    wordsRegexpString = r"\w+"
    wordsRegexp = re.compile(wordsRegexpString)
    wordList = wordsRegexp.findall(text.lower())

    return list(Counter(wordList).items())

def set_association(words, sentence_id, cursor):
    """ 
    Pass in "words" which is a list of tuples - each tuple is word,count
    ("a_word" and count of occurences - i.e. ("the", 3) means the occurred 3 times in sentence)
    Nothing is returned by this function - it just updates the associations table in the database
    
    If current association for a word_id is 0, a new word-sentence association is added
    
    If current association for a word_id is > 0, the word-sentence association is updated with a new weight
    which is just the existing association weight (passed back by get_association) and the new weight
    """
 
    words_length = sum([n * len(word) for word, n in words]) # int giving number of chars in words

    # Looping through Bot-Words, associating them with Human Sentence

    for word, n in words:

        word_id = item_id("word",word,cursor)  # if the ID doesn't exist, a new word + hash ID is inserted
        weight = sqrt(n / float(words_length)) # repeated words get higher weight.  Longer sentences reduces their weight

        #Association shows that a Bot-Word is associated with a Human-Sentence
        # Bot learns by associating our responses with its words

        association = get_association(word_id, sentence_id, cursor)


        # I'm not understanding why we have association > 0. Are we increasing the importance of the association or something??
        # I think I have figured it out. We are reinforcing the word sentence association when it occurs multiple times.
        if association > 0:

            if (DEBUG_ASSOC): 
                print("DEBUG_ASSOC: got an association for", word, "value: ", association," with sentence_id: ",sentence_id)

            SQL_UPDATE = "UPDATE associations SET weight = %s WHERE word_id = %s AND sentence_id = %s"

            if (DEBUG_ASSOC): 
                print("DEBUG_ASSOC:",SQL_UPDATE,weight,word_id,sentence_id)

            cursor.execute(SQL_UPDATE, (association+weight, word_id, sentence_id))

        else:
            SQL_INSERT = "INSERT INTO associations (word_id, sentence_id, weight) VALUES (%s, %s, %s)"
            if (DEBUG_ASSOC): 
                print("DEBUG_ASSOC: ",SQL_INSERT,word_id, sentence_id, weight)
            cursor.execute(SQL_INSERT, (word_id, sentence_id, weight))


def get_association(word_id, sentence_id, curosr):
    """
    Get the weighting associating a Word with a Sentence-Response
    If no association found, return 0
    This is called in the set_association routine to check if there is already an association
    
    associations are referred to in the get_matches() fn, to match input sentences to response sentences
    """

    SQL_SELECT = "SELECT weight FROM associations WHERE word_id =%s AND sentence_id =%s"

    if(DEBUG_ASSOC): 
        print("DEBUG_ASSOC:",SQL_SELECT, word_id, sentence_id)
    curosr.execute(SQL_SELECT, (word_id,sentence_id))

    row = curosr.fetchone()

    if row:
        weight = row["weight"]
    else:
        weight = 0

    return weight

def get_matches(words, cursor):

    """ 
    Retrieve the most likely sentence-answer from the database
    pass in humanWords, calculate a weighting factor for different sentences based on data in associations table  
    """

    results = []
    listSize = 10

    # Removed temp tables due to  GTID configuration issue in mySQL
    #cursor.execute('CREATE TEMPORARY TABLE results(sentence_id TEXT, sentence TEXT, weight REAL)')
    cursor.execute("DELETE FROM results WHERE connection_id = connection_id()")


    # calc "words_length" for weighting calc
    word_length = sum([n * len(word) for word, n in words])

    if (DEBUG_MATCH): 
        print("DEBUG_MATCH: words list", words, "word_length:", word_length)

    for word, n in words:
        #weight = sqrt(n / float(words_length))  # repeated words get higher weight.  Longer sentences reduces their weight
        weight = sqrt(n / float(word_length))
        SQL_INSERT ="""
            INSERT INTO results
            SELECT connection_id(), associations.sentence_id, sentences.sentence, %s * associations.weight / (1 + sentences.used)
            FROM words 
            INNER JOIN associations ON  associations.word_id = words.hashid 
            INNER JOIN sentences ON sentences.hashid = associations.sentence_id 
            WHERE words.word = %s
            """
    
        if (DEBUG_MATCH): 
            print("DEBUG MATCH: ",SQL_INSERT, " weight = ", weight, "word = ", word)
    
        try:
            cursor.execute(SQL_INSERT, (weight, word))
        except Exception as e:
            print(f"Error in Insert: {e}")


    if (DEBUG_MATCH): 
        print("DEBUG MATCH: ",SQL_INSERT)

    try:
        cursor.execute("""
            SELECT sentence_id, sentence, SUM(weight) AS sum_weight 
            FROM results
            WHERE connection_id = connection_id()
            GROUP BY sentence_id, sentence
            ORDER By sum_weight DESC
            """)
    except Exception as e:
        print(f"Error in Select: {e}")


    # Fetch an ordered "listSize" number of results
    try:
        for i in range(0, listSize):
            row = cursor.fetchone()
            if row:
                results.append([row["sentence_id"], row["sentence"], row["sum_weight"]])
                if (DEBUG_MATCH): 
                    print("**",[row["sentence_id"], row["sentence"], row["sum_weight"]],"\n")
            
            else:
                break
    except Exception as e:
        print("Error in fetching results: {e}")

    cursor.execute("DELETE FROM results WHERE connection_id = connection_id()")

    return results

def feedback_stats(sentence_id, cursor, previous_sentence_id = None, sentiment = True):
    """
    Feedback usage of sentence stats, tune model based on user response.
    Simple BOT Version 1 just updates the sentance used counter
    """
    SQL_UPDATE = "UPDATE sentences SET used=used+1 WHERE hashid = %s"
    cursor.execute(SQL_UPDATE,(sentence_id,))

def train_me(inputSentence, responseSentence, cursor):
    inputWords = get_words(inputSentence)
    responseSentenceID = item_id("sentence", responseSentence, cursor)
    set_association(inputWords, responseSentenceID, cursor)

def chat_flow(cursor, humanSentence, weight):

    humanWords = get_words(humanSentence)
    matches = get_matches(humanWords, cursor)
    trainMe = False

    if len(matches)==0:
        botSentence = NO_DATA
        trainMe = True
    else:
        sentence_id, botSentence, weights = matches[0]

        if weights > ACCURACY_THRESHOLD:
            feedback_stats(sentence_id, cursor)
            train_me(botSentence, humanSentence, cursor)

        else:
            botSentence = NO_DATA
            trainMe = True
    
    return botSentence, weight, trainMe


if __name__ == "__main__":

    conf = utils.get_config()

    DBHOST = conf["MySQL"]["server"]
    DBUSER = conf["MySQL"]["dbuser"]
    DBNAME = conf["MySQL"]["dbname"]

    print("Starting Bot...")
    print("Connecting to database...")
    connection = utils.db_connection(DBHOST, DBUSER, DBNAME)
    cursor = connection.cursor()
    connectionID = utils.db_connectionID(cursor)
    print("...connected")

    trainMe = False
    botSentence = "Hello!"

    while True:

        if DEBUG_WEIGHT:
            print("Bot> "+ botSentence + " DEBUG_WEIGHT" + str(round(weight, 5)))
        else:
            print("Bot> "+ botSentence)

        if trainMe:
            print("Bot> Please can you train me - enter a response for me to learn (Enter to skip)")
            previousSentence = humanSentence
            humanSentence = input(">>> ").strip()

            if len(humanSentence) > 0:
                train_me(previousSentence, humanSentence, cursor)
                print("Bot> Thanks I've noted that")
            else:
                print("Bot> Okay, moving on...")
                trainMe = False

        humanSentence = input(">>> ").strip()

        if ((humanSentence == "") or (humanSentence.strip(punctuation).lower() == "quit") or (humanSentence.strip(punctuation).lower() == "exit")):
            break

        botSentence, weight, trainMe = chat_flow(cursor, humanSentence, weight)

        connection.commit()