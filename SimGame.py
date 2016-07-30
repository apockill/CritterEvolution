# 1 - Import library
import FixTk
from Tkinter import Tk
from tkFileDialog import askopenfilename
import pygame
import json
import numpy  as np
import random as r
import os
from math           import sqrt
from scipy.spatial  import cKDTree
from pgu            import text, gui as pgui
from pygame.locals  import *
from Common         import *





class PyObject(object):
    def __init__(self, ID):
        self.ID  = ID
        self.pos = np.asarray([0.0,0.0])
        self.intPos = lambda pos: (int(pos[0]), int(pos[1]))

    def getPos(self):
        return self.pos

    def setPos(self, x, y):
        if x <            0: x = 0
        if y <            0: y = 0
        if x >  gameWidth: x = gameWidth
        if y > gameHeight: y = gameHeight
        self.pos[0] = x
        self.pos[1] = y

    def move(self, x, y):
        self.setPos(self.pos[0] + x, self.pos[1] + y)

    def draw(self, screen):
        pass

    def run(self, shared):
        pass

class Critter(PyObject):
    averageRadius = 12
    geneCount     = 15

    def __init__(self, ID, attributes=None, genes=None, initHealth=None, x=None, y=None):
        PyObject.__init__(self, ID)
        self.tests   = [self.nearestCritter,            # TESTED
                        self.nearestScavenger,          # TESTED
                        self.nearestPredator,           # TESTED
                        self.nearestRelative,           # TESTED
                        self.nearestForeigner,          # TESTED
                        self.nearestFood,               # TESTED
                        self.nearestPlant,              # TESTED
                        self.nearestWall,               # TESTED
                        self.nearestHealth,             # TESTED
                        self.nearestPredHealth,
                        self.nearestScavHealth,
                        self.mySleepiness,              # TESTED
                        self.myHunger,                  # TESTED
                        self.myHealth]                  # TESTED

        self.actions = [
                        self.findAMate,                 # TESTED
                        self.findScavengerMate,         # TESTED
                        self.findPredatorMate,          # TESTED
                        self.attackNearest,             # TESTED
                        self.attackNearestRelative,     # TESTED
                        self.attackNearestForeigner,    # TESTED
                        self.attackNearestScavenger,    # Tested
                        self.attackNearestPredator,     # Tested
                        self.runFromNearest,            # TESTED
                        self.runFromScavenger,          # TESTED
                        self.runFromPredator,           # TESTED
                        self.runFromRelative,           # TESTED
                        self.runFromForeigner,          # TESTED
                        self.runFromWall,               # TESTED
                        self.runFromPlant,              # TESTED
                        self.goToNearestCritter,        # TESTED
                        self.goToNearestPredator,       # TESTED
                        self.goToNearestScavenger,      # TESTED
                        self.goToNearestRelative,       # TESTED
                        self.goToNearestForeigner,      # TESTED
                        self.goToNearestPlant,          # TESTED
                        self.goToNearestWall,           # TESTED
                        self.goToFood,                  # TESTED
                        self.goToBiggestFood,           # TESTED
                        self.goToSmallestFood,
                        self.goToSleep]                 # TESTED


        # Set up Genes and Attributes
        if attributes is None:
            attributes = {"color":              (127, 127, 127),  #r.sample(range(0, 255), 3),
                          "maxHealth": r.randint(50, 150) * 1.0,
                          "relatives":                       [],
                          "generation":                       1,
                          "cumulativeGen":                    1}  # Total generations, even from past saves

        if          x is None: x = r.random() * screenWidth
        if          y is None: y = r.random() * screenHeight
        if      genes is None: self.generateGenes()
        if initHealth is None: initHealth = attributes["maxHealth"] / 2


        # CONSTANTS
        self.distUnit        = ((gameWidth ** 2 + gameHeight ** 2) ** .5 / 2.0) / 100.0
        self.sleepMultiplier = (attributes["maxHealth"] / 100.0)     # Bigger health creatures get tired quicker
        self.speedMultiplier = (100 / attributes["maxHealth"])       #Small ones go faster
        self.punchMultiplier = (attributes["maxHealth"] / 100)       # Bigger ones hurt more

        # Attribute related variables
        self.attributes  = attributes
        self.initHealth  = initHealth
        self.health      = initHealth
        self.radius      = (self.health / 100) * self.averageRadius     # Average radius should be 15

        # State Variables
        self.sleepiness  = 0.0
        self.hunger      = 0
        self.age         = 0
        self.kills       = 0
        self.foodEaten   = 0
        self.mates       = 0
        self.state       = "Awake"
        self.personality = self.getPersonality()


        # Collision checking and how often the critter checks
        self.maxBlind   = 30                       # How many frames the object will go between updating it's collisions
        self.curBlind   = self.ID % self.maxBlind  # How many blind frames has it been
        self.nearest    = {}                       # A dictionary of the nearest object, with the key being type of obj
        self.collisions = {}
        self.curGene    = self.genes[0]            # This is so that I can easily check what gene is currently being run


        # Utility functions
        self.dist         = lambda p1, p2: sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
        self.notRelatives = lambda c1, c2: c1.ID not in c2.attributes["relatives"] and c2.ID not in c1.attributes["relatives"]
        self.setPos(x, y)


    def run(self, shared):
        # print "\nID", obj.ID, "Sleepiness:", int(obj.sleepiness), "\tRadius:", int(obj.radius), "\tHealth:", \
        #     int(obj.health), "\tAge:", obj.age, "\tHunger:", obj.hunger, "\tgen:", obj.attributes["generation"],\
        #     "\tkills:", obj.kills, "\tfoods:", obj.foodEaten, "relatives", len(obj.attributes["relatives"]), \
        #     "personality:", obj.personality

        if self.state == "Dead": return
        self.refreshStats()
        if self.state == "Asleep":  return


        # Run this every step
        if self.curBlind == self.maxBlind:
            self.personality = self.getPersonality()
            self.getNearest()
            self.getCollisions()
            self.curBlind    = 0
        elif self.curBlind % 5 == 0:
            self.updateNearest()  # Update the distances to objects
            self.getCollisions()
        self.curBlind += 1



        for i, gene in enumerate(self.genes):
            if gene["test"](gene["thresh"], gene["sign"]):
                gene["action"]()
                self.curGene = gene
                self.hunger -= .25 * i/(self.geneCount - .9)  # Reward critters that 'think deeper'
                break

        if self.health <= 0: self.kill()

    def setPos(self, x, y):
        xGood = True
        yGood = True
        if Wall in self.nearest:
            for wall, dist in self.nearest[Wall]:
                if dist > 100: break  # if it's too far away to come in contact within five frames.

                if not xGood and not yGood: return
                wx = wall.pos[0]
                wy = wall.pos[1]

                if wx <= x <= wx + Wall.radius and wy <= self.pos[1] <= wy + Wall.radius:
                    xGood = False
                    continue

                if wx <= self.pos[0] <= wx + Wall.radius and wy <= y <= wy + Wall.radius:
                    yGood = False
                    continue


        if not xGood: x = self.pos[0]
        if not yGood: y = self.pos[1]
        PyObject.setPos(self, x, y)


    # TESTS
    def nearestCritter(self, distance, sign):
        return self.nearestTypeTest(Critter, distance, sign)

    def nearestScavenger(self, distance, sign):
        if Critter not in self.nearest:
            if sign == ">": return True
            if sign == "<": return False

        for critter, critDist in self.nearest[Critter]:
            if critter.personality == "Scavenger":
                dist = distance * self.distUnit
                if sign == "<" and critDist < dist: return True
                if sign == ">" and critDist > dist: return True
                break
        return False

    def nearestPredator(self, distance, sign):
        if Critter not in self.nearest:
            if sign == ">": return True
            if sign == "<": return False

        for critter, critDist in self.nearest[Critter]:
            if critter.personality == "Predator":
                dist = distance * self.distUnit
                if sign == "<" and critDist < dist: return True
                if sign == ">" and critDist > dist: return True
                break
        return False

    def nearestRelative(self, distance, sign):
        if Critter not in self.nearest:
            if sign == ">": return True
            if sign == "<": return False

        for critter, critDist in self.nearest[Critter]:
            if not self.notRelatives(self, critter):
                dist = distance * self.distUnit
                if sign == "<" and critDist < dist: return True
                if sign == ">" and critDist > dist: return True
                break
        return False

    def nearestForeigner(self, distance, sign):
        if Critter not in self.nearest:
            if sign == ">": return True
            if sign == "<": return False

        for critter, critDist in self.nearest[Critter]:
            if self.notRelatives(self, critter):
                dist = distance * self.distUnit
                if sign == "<" and critDist < dist: return True
                if sign == ">" and critDist > dist: return True
                break
        return False

    def nearestFood(self, distance, sign):
        return self.nearestTypeTest(Food, distance, sign)

    def nearestPlant(self, distance, sign):
        return self.nearestTypeTest(Plant, distance, sign)

    def nearestWall(self, distance, sign):
        return self.nearestTypeTest(Wall, distance, sign)

    def nearestHealth(self, health, sign):
        # If health of nearest critter is > or < a certain amont.
        if Critter not in self.nearest: return False

        nearestCritter = self.nearest[Critter][0][0]
        healthFrac     = (nearestCritter.health / nearestCritter.attributes["maxHealth"]) * 100.0
        if sign == "<" and healthFrac < health: return True
        if sign == ">" and healthFrac > health: return True

        return False

    def nearestPredHealth(self, health, sign):
        nearestPredator = self.getNearestPersonality("Predator")
        if nearestPredator is None: return False


        healthFrac     = (nearestPredator.health / nearestPredator.attributes["maxHealth"]) * 100.0
        if sign == "<" and healthFrac < health: return True
        if sign == ">" and healthFrac > health: return True

        return False

    def nearestScavHealth(self, health, sign):
        nearestScavenger = self.getNearestPersonality("Scavenger")
        if nearestScavenger is None: return False


        healthFrac     = (nearestScavenger.health / nearestScavenger.attributes["maxHealth"]) * 100.0
        if sign == "<" and healthFrac < health: return True
        if sign == ">" and healthFrac > health: return True

        return False

    def mySleepiness(self, sleepiness, sign):
        return self.myValue(self.sleepiness, sleepiness, sign)

    def myHunger(self, hunger, sign):
        return self.myValue(self.hunger, hunger, sign)

    def myHealth(self, health, sign):
        healthFrac = (self.health / self.attributes["maxHealth"]) * 100.0
        return self.myValue(healthFrac, health, sign)


    # ACTIONS
    def findAMate(self):
        # Find a mate that is NOT a relative
        if Critter in self.collisions:
            self.mate(self.getBestMateCollisions())
            return

        if Critter in self.nearest:
            self.moveTowards(self.getBestMateNearest())  # If no critter nearby matches the criteria, go by one anyways

    def findScavengerMate(self):
        # Find a mate that is NOT a relative
        if Critter in self.collisions:
            self.mate(self.getBestMateCollisions(personalityType="Scavenger"))
            return

        if Critter in self.nearest:
            self.moveTowards(self.getBestMateNearest(personalityType="Scavenger"))
            return

    def findPredatorMate(self):
        # Find a mate that is NOT a relative
        if Critter in self.collisions:
            self.mate(self.getBestMateCollisions(personalityType="Predator"))
            return

        if Critter in self.nearest:
            self.moveTowards(self.getBestMateNearest(personalityType="Predator"))
            return

    def attackNearest(self):
        if Critter in self.collisions:
            self.attack(self.collisions[Critter][0])
        elif Critter in self.nearest:
            self.moveTowards(self.nearest[Critter][0][0])

    def attackNearestRelative(self):
        nearestRelative = self.getNearestRelative()

        if Critter in self.collisions and nearestRelative in self.collisions[Critter]:
            self.attack(nearestRelative)
        else:
            self.moveTowards(nearestRelative)

    def attackNearestForeigner(self):
        nearestForeigner = self.getNearestForeigner()

        if Critter in self.collisions and nearestForeigner in self.collisions[Critter]:
            self.attack(nearestForeigner)
        else:
            self.moveTowards(nearestForeigner)

    def attackNearestScavenger(self):
        nearestScavenger = self.getNearestPersonality("Scavenger")

        if Critter in self.collisions and nearestScavenger in self.collisions[Critter]:
            self.attack(nearestScavenger)
        else:
            self.moveTowards(nearestScavenger)

    def attackNearestPredator(self):
        nearestPredator = self.getNearestPersonality("Predator")

        if Critter in self.collisions and nearestPredator in self.collisions[Critter]:
            self.attack(nearestPredator)
        else:
            self.moveTowards(nearestPredator)

    def runFromNearest(self):
        self.moveAway(self.getNearestType(Critter))

    def runFromScavenger(self):
        self.moveAway(self.getNearestPersonality("Scavenger"))

    def runFromPredator(self):
        self.moveAway(self.getNearestPersonality("Predator"))

    def runFromRelative(self):
        self.moveAway(self.getNearestRelative())

    def runFromForeigner(self):
        self.moveAway(self.getNearestForeigner())

    def runFromWall(self):
        self.moveAway(self.getNearestType(Wall))

    def runFromPlant(self):
        self.moveAway(self.getNearestType(Plant))

    def goToNearestCritter(self):
        if Critter in self.collisions:
            return
        if Critter in self.nearest:
            self.moveTowards(self.nearest[Critter][0][0])

    def goToNearestPredator(self):
        nearestPredator = self.getNearestPersonality("Predator")

        if nearestPredator in self.collisions: return

        if Critter in self.nearest:
            self.moveTowards(nearestPredator)

        if Critter in self.nearest:
            self.moveTowards(self.getNearestPersonality("Predator"))

    def goToNearestScavenger(self):
        nearestScavenger = self.getNearestPersonality("Scavenger")

        if nearestScavenger in self.collisions: return

        if Critter in self.nearest:
            self.moveTowards(nearestScavenger)

    def goToNearestRelative(self):
        nearestRelative = self.getNearestRelative()

        if nearestRelative in self.collisions: return

        if Critter in self.nearest:
            self.moveTowards(nearestRelative)

    def goToNearestForeigner(self):
        nearestForeigner = self.getNearestForeigner()

        if nearestForeigner in self.collisions: return

        if Critter in self.nearest:
            self.moveTowards(nearestForeigner)

    def goToNearestPlant(self):
        if Plant in self.collisions:
            return
        if Plant in self.nearest:
            self.moveTowards(self.nearest[Plant][0][0])

    def goToNearestWall(self):
        if Wall in self.collisions:
            return
        if Wall in self.nearest:
            self.moveTowards(self.nearest[Wall][0][0])

    def goToFood(self):
        if Food in self.collisions:
            self.eatFood(self.collisions[Food][0])
        elif Food in self.nearest:
            nearestFood = self.nearest[Food][0][0]
            self.moveTowards(nearestFood)

    def goToBiggestFood(self):
        if Food not in self.nearest: return

        bestNutrition = 0
        bestFood = None
        for food, foodDist in self.nearest[Food]:
            if food.nutrition > bestNutrition:
                bestNutrition = food.nutrition
                bestFood = food


        if bestFood is None: return

        if Food in self.collisions and bestFood in self.collisions[Food]:
            self.eatFood(bestFood)
        else:
            self.moveTowards(bestFood)

    def goToSmallestFood(self):
        if Food not in self.nearest: return

        worstNutrition = 1000000
        worstFood = None
        for food, foodDist in self.nearest[Food]:
            if food.nutrition < worstNutrition:
                worstNutrition = food.nutrition
                worstFood = food


        if worstFood is None: return

        if Food in self.collisions and worstFood in self.collisions[Food]:
            self.eatFood(worstFood)
        else:
            self.moveTowards(worstFood)

    def goToSleep(self):
        self.state = "Asleep"


    # BUILDER FUNCTIONS FOR TESTS/ACTIONS
    def myValue(self, value, thresh, sign):
        if sign == "<" and value < thresh: return True
        if sign == ">" and value > thresh: return True
        return False

    def nearestTypeTest(self, objType, distance, sign):
        if objType not in self.nearest:
            if sign == ">": return True
            if sign == "<": return False

        for obj, objDist in self.nearest[objType]:
            dist = distance * self.distUnit
            if sign == "<" and objDist < dist: return True
            if sign == ">" and objDist > dist: return True
            break
        return False

    def getNearestType(self, objType):
        if objType in self.nearest:
            return self.nearest[objType][0][0]
        return None

    def getBestMateNearest(self, personalityType=None):
        bestAge = 0
        bestCritter = None

        for critter, critDist in self.nearest[Critter]:
            # if critter.health < critter.attributes["maxHealth"]: continue

            if personalityType is None or personalityType == critter.personality:
                if self.notRelatives(self, critter):
                    if critter.age > bestAge:
                        bestAge = critter.age
                        bestCritter = critter

        return bestCritter

    def getBestMateCollisions(self, personalityType=None):
        bestAge  = 0
        bestCritter = None

        for critter in self.collisions[Critter]:
            # if critter.health < critter.attributes["maxHealth"]: continue
            if personalityType is None or personalityType == critter.personality:
                if self.notRelatives(self, critter):
                    if critter.age > bestAge:
                        bestAge = critter.age
                        bestCritter = critter
        return bestCritter

    def getNearestRelative(self):
        if Critter not in self.nearest: return

        for critter, critDist in self.nearest[Critter]:
            if not self.notRelatives(self, critter):
                return critter

    def getNearestForeigner(self):
        if Critter not in self.nearest: return

        for critter, critDist in self.nearest[Critter]:
            if self.notRelatives(self, critter):
                return critter

    def getNearestPersonality(self, personality):
        if Critter not in self.nearest: return None

        for critter, critDist in self.nearest[Critter]:
            if critter.personality == personality:
                return critter


    # Critter Specific
    def refreshStats(self):

        # if self.hunger < 0:     print "HUNGER NEGATIVE"
        # if self.sleepiness < 0: print "SLEEPINESS NEGATIVE"
        self.age    += 1
        if self.age > 3500 and self.sleepiness >= 0:
            # Sleepiness is only ever negative after having mated. This ensures that critters that are old but not mating
            # face an inherent disadvantage.
            self.health -= self.age / 35000.0

        if self.hunger >= 100:
            self.health -= .08 * (int(self.hunger / 50))


        if self.state == "Awake":
            self.hunger += .5
            self.sleepiness += .1 * self.sleepMultiplier  # Minimum sleep incriment
            if self.sleepiness >= 100: self.state = "Asleep"

        if self.state == "Asleep":
            self.hunger += .25
            if self.sleepiness <= 0:
                self.state = "Awake"
            else:
                self.sleepiness -= .5


        self.health = clamp(self.health,  0, self.attributes["maxHealth"])

        healthFrac  = self.health / self.attributes["maxHealth"]
        self.radius = (self.health / 100) * self.averageRadius
        self.speed  = (1.0 + self.speedMultiplier) * healthFrac + 1  # Even at lowest health, speed will be .333333

        # Keep the numbers within the range
        # self.radius = clamp(self.radius,  3, self.attributes["maxRadius"])
        # self.speed  = clamp(self.speed,  .1, self.attributes["maxSpeed"])

    def kill(self):
        if self.initHealth > 0: # If you have initHealth < 0, you were already sucked dry by attackers for food.
            objects.add(Food(objects.nextID, self.initHealth, self.attributes["color"], x=self.pos[0], y=self.pos[1]))

        self.nearest    = -1  # Prevent memory leaks
        self.collisions = -1
        self.state = "Dead"
        objects.delete(self)

    def attack(self, critObj):
        # When a critter is attacked, it must calculate the damage to itself
        if critObj is None: return
        if not objects.existsObj(critObj): return

        if critObj.health > self.punchMultiplier:
            healthGain = self.punchMultiplier
        else:
            healthGain = critObj.health

        critObj.health     -= healthGain
        critObj.initHealth  = clamp(critObj.initHealth - healthGain, 0, 100000)

        self.gainHealth(healthGain)

        if critObj.health <= 0:
            self.hunger      -= 50
            self.kills += 1
            critObj.kill()

    def gainHealth(self, amount):
        self.health += amount
        hungerLoss = int(round(amount * 2 + .51, 0)) * 6 + 5
        if self.hunger - hungerLoss > 0:
            self.hunger -= hungerLoss
            if self.health == self.attributes["maxHealth"]: self.hunger = 0

    def eatFood(self, foodObj):
        if not objects.existsObj(foodObj): return
        if self.health == self.attributes["maxHealth"]:
            return

        gainHealth = foodObj.extract(self.attributes["maxHealth"] - self.health)



        if gainHealth is not None:
            if objects.existsObj(foodObj):
                self.foodEaten += 1

            self.gainHealth(gainHealth)

    def mate(self, mateCritter):
        if mateCritter is None: return
        if mateCritter in self.attributes["relatives"]: print "ERROR: INCEST ALERT! 1"
        if self in mateCritter.attributes["relatives"]: print "ERROR: INCEST ALERT! 2"

        if self.health < 40 or mateCritter.health < 40: return # If the parents are just too unhealthy to even attempt
        # Check if these two are able to contribute enough health for the baby to be born
        herAttr = mateCritter.attributes
        hisAttr = self.attributes


        # Get new max health
        herMaxHealth  = herAttr["maxHealth"]
        hisMaxHealth  = hisAttr["maxHealth"]
        newMaxHealth  = (herMaxHealth + hisMaxHealth)*.5+ r.randint(-35, 35)
        newMaxHealth  = clamp(newMaxHealth, 50, 150)
        newInitHealth = newMaxHealth * .5
        if mateCritter.health + self.health > newInitHealth:
            totalHealth        = mateCritter.health + self.health
            selfGiveHealth     = newInitHealth * (       self.health / totalHealth)
            mateGiveHealth     = newInitHealth * (mateCritter.health / totalHealth)

            if selfGiveHealth + mateGiveHealth < newInitHealth: return

            if        self.health - selfGiveHealth <= 0: return
            if mateCritter.health - mateGiveHealth <= 0: return
            self.health            -= selfGiveHealth
            self.initHealth         = clamp(       self.initHealth - selfGiveHealth, 0, 100000)
            mateCritter.health     -= mateGiveHealth
            mateCritter.initHealth  = clamp(mateCritter.initHealth - mateGiveHealth, 0, 100000)
            self.mates += 1
        else: return



        # Generation Count
        herGeneration = herAttr["generation"]
        hisGeneration = hisAttr["generation"]
        newGeneration = (hisGeneration, herGeneration)[herGeneration >= hisGeneration] + 1

        # Cumulative Generation Count
        herCumulative = herAttr["cumulativeGen"]
        hisCumulative = hisAttr["cumulativeGen"]
        newCumulative = (hisCumulative, herCumulative)[herCumulative >= hisCumulative]


        # Get relatives list
        herRelatives = herAttr["relatives"]
        hisRelatives = hisAttr["relatives"]
        newRelatives = [self.ID, mateCritter.ID]
        for i in range(0, len(herRelatives) + len(hisRelatives)):
            if len(newRelatives) >= 50: break

            if  i < len(herRelatives):
                if objects.existsID(herRelatives[i]) or i < 5:
                    if herRelatives[i] not in newRelatives:
                        newRelatives.append(herRelatives[i])

            if i < len(hisRelatives):
                if objects.existsID(hisRelatives[i]) or i < 5:
                    if hisRelatives[i] not in newRelatives:
                        newRelatives.append(hisRelatives[i])

        # Get new Attributes
        newAttributes = {        "color":      (0, 0, 0),  # Placeholder color until 'mutations' are counted out
                             "maxHealth":   newMaxHealth,
                             "relatives":   newRelatives,
                            "generation":  newGeneration,
                         "cumulativeGen":  newCumulative}


        # Generate new genes
        newObj = Critter(objects.nextID, attributes=newAttributes,
                         initHealth=newInitHealth, x=self.pos[0], y=self.pos[1])
        newGenes = []
        herGene = mateCritter.genes
        hisGene = self.genes
        mutationCount = 0.0
        heritageCount = 0.0 #So if there are more genes from him, it'll be negative. More genes from her, it'll be +
        for i in range(0, self.geneCount):
            newGene = {}

            sameTestGene = herGene[i]["test"].__name__ == hisGene[i]["test"].__name__
            if sameTestGene:
                testFunc          = r.choice([herGene[i]["test"].__name__, hisGene[i]["test"].__name__])
                newGene["thresh"] = r.choice([herGene[i]["thresh"], hisGene[i]["thresh"]])
                newGene["sign"]   = r.choice([  herGene[i]["sign"],   hisGene[i]["sign"]])
                actionFunc        = r.choice([herGene[i]["action"].__name__, hisGene[i]["action"].__name__])
            else:
                chosenGene        = r.choice([herGene[i], hisGene[i]])
                if chosenGene in herGene:
                    heritageCount += 1
                if chosenGene in hisGene:
                    heritageCount -= 1
                testFunc          = chosenGene["test"].__name__
                newGene["thresh"] = chosenGene["thresh"]
                newGene["sign"]   = chosenGene["sign"]
                actionFunc        = chosenGene["action"].__name__



            # Mutate the genes a little bit
            if r.randint(0, 100) < 2.5:
                mutationCount + 1.5
                newGene["thresh"] += r.randint(-5, 5)

            if r.randint(0, 100) < 1.5:
                mutationCount += 3
                newGene["sign"] = r.choice(["<", ">"])

            if r.randint(0, 100) < 1:
                mutationCount += 5
                testFunc        = r.choice(self.tests).__name__
            if r.randint(0, 100) < 1:
                mutationCount += 5
                actionFunc      = r.choice(self.actions).__name__

            newGene["thresh"] = clamp(newGene["thresh"], 0.0, 100.0)
            newGene["test"]   = getattr(newObj, testFunc)
            newGene["action"] = getattr(newObj, actionFunc)
            newGenes.append(newGene)


        #Sometimes swap one set of genes
        if r.randint(0, 100) < 5:
            mutationCount += 10
            swapFrom = r.randint(0, len(newGenes)-1)
            swapTo   = r.randint(0, len(newGenes)-1)
            replaced = newGenes[swapTo]
            newGenes[swapTo] = newGenes[swapFrom]
            newGenes[swapFrom] = replaced


        # Get mixed color. Color will deviate more if there have been more mutations!
        herColor = herAttr["color"]
        hisColor = hisAttr["color"]
        if -1 <= heritageCount <= 1:  # If they are very close, average their colors
            newColor = [int((herColor[0] + hisColor[0]) / 2.0),
                        int((herColor[1] + hisColor[1]) / 2.0),
                        int((herColor[2] + hisColor[2]) / 2.0)]
        if heritageCount < -1:
            newColor = [hisColor[0], hisColor[1], hisColor[2]]
        if heritageCount > 1:
            newColor = [herColor[0], herColor[1], herColor[2]]
        if mutationCount > 2:
            newColor[0] += r.choice([-mutationCount * 2.0, mutationCount * 2.0])
            newColor[1] += r.choice([-mutationCount * 2.0, mutationCount * 2.0])
            newColor[2] += r.choice([-mutationCount * 2.0, mutationCount * 2.0])

        newColor = (clamp(newColor[0], 0, 255),
                    clamp(newColor[1], 0, 255),
                    clamp(newColor[2], 0, 255))


        # Finilize the object and add it.
        newObj.attributes["color"] = newColor
        newObj.genes = newGenes
        newObj.fixUselessGenes()
        newObj.fixUselessGenes()
        objects.add(newObj)

    def moveTowards(self, object):
        # if objType not in nearest: return  #There are none of those objects on the map
        # Will move towards the nearest object of 'type'
        if object is None: return

        hMove = object.pos[0] - self.pos[0]
        vMove = object.pos[1] - self.pos[1]
        if hMove == 0 and vMove == 0: return

        mag   = sqrt(hMove**2 + vMove**2)
        hMove = (hMove / mag) * self.speed
        vMove = (vMove / mag) * self.speed

        # self.sleepiness += .2 * self.sleepMultiplier
        self.move(hMove, vMove)

    def moveAway(self, object):
        if object is None: return

        hMove = object.pos[0] - self.pos[0]
        vMove = object.pos[1] - self.pos[1]
        if hMove == 0 and vMove == 0: return

        mag   = sqrt(hMove**2 + vMove**2)
        hMove = (hMove / mag) * self.speed
        vMove = (vMove / mag) * self.speed

        # self.sleepiness += .2 * self.sleepMultiplier
        self.move(-hMove, -vMove)


    # Collision and sight
    def fixUselessGenes(self):
        for i in range(1, self.geneCount):
            currGene = self.genes[i]
            numberOfOthers = 0

            # If there are already two of the same test previously, then just pick a new one for this
            for k in range(0, i):
                if self.genes[k]["test"] == currGene["test"]: numberOfOthers += 1
            if numberOfOthers >= 2: self.genes[i]["test"]  = r.choice(self.tests)


            for j in range(0, i):
                prevGene  = self.genes[j]
                prevTest  = prevGene["test"]
                currTest  = currGene["test"]
                if prevTest == currTest:
                    prevSign   = prevGene["sign"]
                    currSign   = currGene["sign"]
                    prevThresh = prevGene["thresh"]
                    currThresh = currGene["thresh"]

                    if prevSign == currSign:
                        if prevSign == "<" and prevThresh >= currThresh: self.genes[i]["sign"] = ">"
                        if prevSign == ">" and prevThresh <= currThresh: self.genes[i]["sign"] = "<"

    def getPersonality(self):
        kills = 0
        foods  = 0

        # if there's not a good sample size, estimate using parents
        if (self.kills <= 5 and self.foodEaten <= 5) and len(self.attributes["relatives"]) >= 2:
            for parent in range(0, 2):
                obj = objects.get(self.attributes["relatives"][parent])
                if obj is None: return
                kills += obj.kills
                foods += obj.foodEaten

        kills += self.kills
        foods += self.foodEaten

        if kills > foods:
            return "Predator"
        else:
            return "Scavenger"

    def getCollisions(self):
        # Returns a dictionary of collisions of the format [foodObj, critterObj]
        # {Critters: nearestCritter, Food: nearestFood}
        if self.collisions == -1: print "ERROR: Collisions being checked"
        self.collisions = {}
        for objType in self.nearest:
            for obj, objDist in self.nearest[objType]:
                if objDist < (self.radius + 6 + obj.radius):
                    if objType in self.collisions:
                        self.collisions[objType].append(obj)
                    else:
                        self.collisions[objType] = [obj]

    def getNearest(self):
        # Returns a dictionary of objects in order from distance, seperated by type in the following format.
        # {Critters: nearestCritter, Food: nearestFood}
        if self.nearest == -1: print "ERROR: Nearest being checked"
        self.nearest = {}
        for objType in objects.kdTrees:
            nearestObjs = objects.getNeighborsSorted(self.ID, objType)

            if nearestObjs is None: continue

            for id, dist in nearestObjs:
                objTag = (objects.get(id), dist)

                if objTag[0] is None or self == objTag[0]: continue  # If object has disappeared or is self, ignore

                if type(objTag[0]) in self.nearest:
                    self.nearest[type(objTag[0])].append(objTag)
                else:
                    self.nearest[type(objTag[0])] = [objTag]

    def updateNearest(self):
        # Updates the distances in self.nearest, without searching again for all objects
        for objType in self.nearest:
            for i in range(0, len(self.nearest[objType])):
                obj = self.nearest[objType][i][0]
                self.nearest[objType][i] = (obj, self.dist(obj.getPos(), self.getPos()))
            self.nearest[objType] = sorted(self.nearest[objType], key= lambda label: label[1])

    def generateGenes(self):
        # Used for 'new' critters that have no genes fed to them
        self.genes = []

        for i in range(self.geneCount):
            test = r.choice(self.tests)
            thresh = r.random() * 100
            sign = r.choice(["<", ">"])
            action = r.choice(self.actions)

            genes = {  "test":    test,
                     "thresh":  thresh,
                       "sign":    sign,
                     "action":  action}
            self.genes.append(genes)

        # Increase likelyhood that the Critter has a findAMate or variant action inside it
        # self.genes[r.randint(0, self.geneCount - 1)]["action"] = r.choice([self.findAMate,
        #                                                                    self.findPredatorMate,
        #                                                                    self.findScavengerMate])

        # Iron out redundancies in the genes
        self.fixUselessGenes()
        self.fixUselessGenes()

    # Window and Controls
    def printGenes(self):
        # Prints the genes in a pretty manner
        print "\n"
        for i in range(0, len(self.genes)):
            print str(i + 1) + ") If",
            print self.genes[i]["test"].__name__,
            print self.genes[i]["sign"],
            print int(self.genes[i]["thresh"]), "then",
            print self.genes[i]["action"].__name__

    def draw(self, screen):
        pygame.draw.circle(screen, self.attributes["color"], self.intPos(self.getPos()), int(self.radius) + 3)

    def getSaveData(self):
        saveData = {}

        # Create genes savedata
        geneSave = []
        for gene in self.genes:
            geneDict = {}
            geneDict["test"]   = gene["test"].__name__
            geneDict["thresh"] = gene["thresh"]
            geneDict["sign"]   = gene["sign"]
            geneDict["action"] = gene["action"].__name__

            geneSave.append(geneDict)
        saveData["genes"] = geneSave


        # Create the attributes saveData
        newAttributes = {"color":          self.attributes["color"],
                          "maxHealth": self.attributes["maxHealth"],
                          "relatives":                           [],
                          "generation":                           1,
                          "cumulativeGen": self.attributes["generation"] + self.attributes["cumulativeGen"]}
        saveData["attributes"] = newAttributes



        return saveData

    def loadSaveData(self, saveData):
        newGenes = []
        for gene in saveData["genes"]:
            newGene = {}
            newGene["test"]   = getattr(self, gene["test"])
            newGene["sign"]   = gene["sign"]
            newGene["thresh"] = gene["thresh"]
            newGene["action"] = getattr(self, gene["action"])
            newGenes.append(newGene)

        self.attributes = saveData["attributes"]
        self.genes = newGenes

        self.initHealth = self.attributes["maxHealth"] / 2.0
        self.health     = self.initHealth
        self.sleepMultiplier = (self.attributes["maxHealth"] / 100.0)     # Bigger health creatures get tired quicker
        self.speedMultiplier = (100 / self.attributes["maxHealth"])       #Small ones go faster
        self.punchMultiplier = (self.attributes["maxHealth"] / 100)       # Bigger ones hurt more
        self.radius      = (self.health / 100) * self.averageRadius     # Average radius should be 15
        print "loaded", self.attributes

class Food(PyObject):

    def __init__(self, ID, nutrition, color=(0,0,0), x=None, y=None):
        if x is None: x = r.random() * screenWidth
        if y is None: y = r.random() * screenHeight

        PyObject.__init__(self, ID)

        self.nutrition = nutrition
        self.radius    = (self.nutrition / 100) * Critter.averageRadius
        self.color     = color


        self.setPos(x, y)

    def extract(self, extractGoal):
        # Extract health from self and give it to a Critter that is eating
        giveNutrition = 0
        if self.nutrition >= extractGoal:
            giveNutrition = extractGoal
        else:
            giveNutrition = self.nutrition


        self.nutrition -= giveNutrition

        if self.nutrition == 0:
            objects.delete(self)
        self.radius = (self.nutrition / 100) * Critter.averageRadius

        return giveNutrition

    def draw(self, screen):
        if self.nutrition == 0:
            objects.delete(self)
        pygame.draw.circle(screen, self.color, self.intPos(self.getPos()), int(self.radius) + 2, 2)

class Wall(PyObject):
    color  = (30, 30, 30)
    radius = 45

    def __init__(self, ID, x, y):
        PyObject.__init__(self, ID)
        x = x - x % self.radius
        y = y - y % self.radius
        self.setPos(int(x), int(y))

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.pos[0], self.pos[1], self.radius, self.radius), 0)

class Plant(PyObject):
    color  = (30, 255, 30)
    radius = 45
    spawnRadius = 100

    def __init__(self, ID, x, y):
        PyObject.__init__(self, ID)

        x -= x % self.radius
        y -= y % self.radius

        self.setPos(int(x), int(y))

    def run(self, shared):
        if shared["energy"] < shared["energyCap"] - 100:
            # x = self.pos[0] + self.radius/2 + r.uniform(-1, 1)*self.spawnRadius
            # y = self.pos[1] + self.radius/2 + r.uniform(-1, 1)*self.spawnRadius

            x = self.pos[0] + self.radius/2 + r.normalvariate(15, self.spawnRadius)*r.choice([-.5, .5])
            y = self.pos[1] + self.radius/2 + r.normalvariate(15, self.spawnRadius)*r.choice([-.5, .5])

            objects.add(Food(objects.nextID, 100, color=(0,0,0), x=x, y=y))

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.pos[0], self.pos[1], self.radius, self.radius), 0)



class MainWindow:
    maxBlind        = 30
    frames          = 0
    fps             = 0.0
    renderScreen    = True
    menuMode        = "PLACE"   # Can be: "place" or "best", meaning it will show different buttons.
    selected        = None
    selectedData    = None      # The "savedata" for the selected critter (or the latest loaded critter)
    bestOfAll       = {"age": None, "lineage": None, "mate": None, "pred": None, "scav": None}  # Best critters of all time in each category

    mouseMode       = "critter" # What mode the mouse is on (1 is first button, 2 is second, and so on)
    rndr            = []        # A list of (object, coords) for drawScreen to do self.screen.blit( object, coords, layer)
    shared          = {"energyCap": 30000, "critterCap": 600, "energy": 0}
    curEnergy       = 0

    textColor       = (255, 255, 255)
    toolbarHeight   = 65
    minScreenWidth  = 640
    minScreenHeight = 480
    infoBoxWidth    = 250
    infoBoxHeight   = 450

    def __init__(self):

        pygame.init()
        pygame.font.init()
        self.container = None

        self.screen  = pygame.display.set_mode((screenWidth, screenHeight), HWSURFACE | DOUBLEBUF | RESIZABLE)
        self.infoBox = None

        self.fnt   = pygame.font.SysFont("monospace", 18)

        self.gui   = pgui.App()  #theme=pgui.Theme(dirs="default")
        self.initUI()

    def initUI(self):
        print "MainWindow.initUI(): Initializing UI"
        spacer = lambda: self.table.add(pgui.Spacer(widthBetween, 0))
        self.infoBox = pygame.Surface((self.infoBoxWidth, self.infoBoxHeight), pygame.SRCALPHA, 32)
        self.infoBox.fill((60, 60, 60, 220))
        self.infoBox = (self.infoBox, (gameWidth - self.infoBoxWidth, gameHeight - self.infoBoxHeight) , -1)

        # Create buttons
        select_move_btn    = pgui.Button("Select")
        render_screen_btn  = pgui.Button("Render")
        save_critter_btn   = pgui.Button("Save")
        load_critter_btn   = pgui.Button("Load")
        mode_menu_btn      = pgui.Button(self.menuMode)
        select_move_btn.connect(   pgui.CLICK, self.btnPressed, "select")
        render_screen_btn.connect( pgui.CLICK, self.btnPressed, "render")
        save_critter_btn.connect(  pgui.CLICK, self.btnPressed, "save")
        load_critter_btn.connect(  pgui.CLICK, self.btnPressed, "load")
        mode_menu_btn.connect(     pgui.CLICK, self.btnPressed, "cycleMode")

        # Create Sliders
        energy_slider = pgui.HSlider(value=self.shared["energyCap"], min=0, max=100000, size=10, width=50, height=16)
        energy_slider.connect(pgui.CHANGE, self.sliderChange, (energy_slider, "energy_slider"))

        # Create labels
        energy_slider_label = pgui.Label("Energy", color=(255, 255, 255))

        widthBetween = 7
        # ROW 1
        self.table = pgui.Table()
        self.table.tr()
        self.table.add(pgui.Spacer(0, gameHeight))  # Spacer top
        self.table.tr()
        self.table.add(pgui.Spacer(10, 0))

        self.table.add(select_move_btn)
        spacer()
        self.table.add(render_screen_btn)
        spacer()
        self.table.add(save_critter_btn)
        spacer()
        self.table.add(load_critter_btn)
        spacer()
        self.table.add(mode_menu_btn)
        spacer()
        self.table.add(energy_slider_label)
        spacer()
        self.table.add(energy_slider)



        # ROW 2
        self.table.add(pgui.Spacer(gameWidth, 10))
        self.table.tr()
        self.table.add(pgui.Spacer(0, 10))
        self.table.tr()
        self.table.add(pgui.Spacer(10, 0))

        if self.menuMode == "PLACE":
            spawn_critter_btn  = pgui.Button("Critter")
            spawn_food_btn     = pgui.Button("Food")
            spawn_wall_btn     = pgui.Button("Wall")
            spawn_plant_btn    = pgui.Button("Plant")
            spawn_critter_btn.connect( pgui.CLICK, self.btnPressed, "critter")
            spawn_food_btn.connect(    pgui.CLICK, self.btnPressed, "food")
            spawn_wall_btn.connect(    pgui.CLICK, self.btnPressed, "wall")
            spawn_plant_btn.connect(   pgui.CLICK, self.btnPressed, "plant")
            self.table.add(spawn_critter_btn)
            spacer()
            self.table.add(spawn_food_btn)
            spacer()
            self.table.add(spawn_wall_btn)
            spacer()
            self.table.add(spawn_plant_btn)
            spacer()

        if self.menuMode == "FIND":
            live_oldest_btn    = pgui.Button("Oldest")
            live_lineage_btn   = pgui.Button("Lineage")
            live_mate_btn      = pgui.Button("Mate")
            live_pred_btn      = pgui.Button("Pred")
            live_scav_btn      = pgui.Button("Scav")
            live_oldest_btn.connect(   pgui.CLICK, self.btnPressed, "live_oldest")
            live_lineage_btn.connect(  pgui.CLICK, self.btnPressed, "live_lineage")
            live_mate_btn.connect(     pgui.CLICK, self.btnPressed, "live_mate")
            live_pred_btn.connect(     pgui.CLICK, self.btnPressed, "live_pred")
            live_scav_btn.connect(     pgui.CLICK, self.btnPressed, "live_scav")

            self.table.add(live_oldest_btn)
            spacer()
            self.table.add(live_lineage_btn)
            spacer()
            self.table.add(live_mate_btn)
            spacer()
            self.table.add(live_pred_btn)
            spacer()
            self.table.add(live_scav_btn)

        if self.menuMode == "BEST":
            best_oldest_btn    = pgui.Button("*Oldest*")
            best_lineage_btn   = pgui.Button("*Lineage*")
            best_mate_btn      = pgui.Button("*Mate*")
            best_pred_btn      = pgui.Button("*Pred*")
            best_scav_btn      = pgui.Button("*Scav*")
            best_oldest_btn.connect(   pgui.CLICK, self.btnPressed, "best_oldest")
            best_lineage_btn.connect(  pgui.CLICK, self.btnPressed, "best_lineage")
            best_mate_btn.connect(     pgui.CLICK, self.btnPressed, "best_mate")
            best_pred_btn.connect(     pgui.CLICK, self.btnPressed, "best_pred")
            best_scav_btn.connect(     pgui.CLICK, self.btnPressed, "best_scav")

            self.table.add(best_oldest_btn)
            spacer()
            self.table.add(best_lineage_btn)
            spacer()
            self.table.add(best_mate_btn)
            spacer()
            self.table.add(best_pred_btn)
            spacer()
            self.table.add(best_scav_btn)


        pygame.display.set_caption('Evo Critters')
        self.gui.init(self.table)


    def run(self):
        # crit1 = Critter(objects.nextID, x=50, y=50)
        # crit1.genes = [{"test": crit1.nearestFood, "sign": "<", "thresh": 98, "action": crit1.goToSmallestFood}]
        # objects.add(crit1)

        #
        # crit2 = Critter(objects.nextID, x=gameWidth - 50, y=gameHeight - 50)
        # crit2.attributes["relatives"] = [crit1.ID]
        # # crit2.kills = 500
        # crit2.foodEaten = 500
        # crit2.genes = [{"test": crit2.nearestCritter, "sign": "<", "thresh": 50, "action": crit2.goToFood}]
        # objects.add(crit2)
        #
        # crit3 = Critter(objects.nextID, x=gameWidth - 50, y=50)
        # crit3.kills = 500
        # crit3.genes = [{"test": crit2.nearestCritter, "sign": "<", "thresh": 50, "action": crit2.goToFood}]
        # objects.add(crit3)

        while True:
            startTime = time()
            self.rndr = []

            ######################  DO ACTUAL GAME STUFF  ######################
            # Get events
            self.handleEvents()


            # Do collision checking for objects every 30 frames
            if self.frames % self.maxBlind == 0:
                objects.generateKDTree()  # Generate a fast numpy array of locations
            self.frames += 1


            # Run all objects
            for obj in objects:
                if not objects.existsObj(obj): continue
                # if type(obj) is Critter: newEnergy += obj.initHealth + obj.health
                # if type(obj) is Food:    newEnergy += obj.nutrition
                obj.run(self.shared)


            # Do all sorts of things that have to be done to guage the game
            newEnergy = 0
            for obj in objects:
                if type(obj) is Critter: newEnergy += obj.initHealth + obj.health
                if type(obj) is Food:    newEnergy += obj.nutrition

                # Compare critter to the best critters of all time, every maxBlind frames
                if type(obj) is Critter and self.frames % self.maxBlind == 0:
                    if None in self.bestOfAll.values():
                        for key in self.bestOfAll: self.bestOfAll[key] = obj


                    if obj.age >= self.bestOfAll["age"].age:
                        self.bestOfAll["age"]     = obj

                    if obj.attributes["generation"] >= self.bestOfAll["lineage"].attributes["generation"]:
                        self.bestOfAll["lineage"] = obj

                    if obj.mates >= self.bestOfAll["mate"].mates:
                        self.bestOfAll["mate"]    = obj

                    if obj.kills >= self.bestOfAll["pred"].kills:
                        self.bestOfAll["pred"]    = obj

                    if obj.foodEaten >= self.bestOfAll["scav"].foodEaten:
                        self.bestOfAll["scav"]    = obj

            self.shared["energy"] = newEnergy


            # Handle mouseMode events
            if keys["mousePos"][1] < gameHeight:
                self.mouseLeft()
                self.mouseRight()


            ######################  UPDATE THE SCREEN  ######################
            if self.renderScreen:
                self.drawUIStats()
                self.drawScreen()
                self.fps =  round(((1 / (time() - startTime + .0000001)) + self.fps) / 2, 1)  # Average last and current


    def drawScreen(self):
        # Draw every object below everything while simultaneously getting the energy of the system

        self.screen.fill((47, 141, 255))
        for obj in objects:
            obj.draw(self.screen)


        self.rndr = sorted(self.rndr, key=lambda i: i[2])
        for drawthing, coords, layer in self.rndr:
            if isinstance(drawthing, type(lambda:0)):
                drawthing(coords)
                continue
            self.screen.blit( drawthing, coords)

        self.gui.paint(self.screen)
        pygame.display.flip()    # Update the screen

    def drawUIStats(self):
        if not self.renderScreen: return
        fnt = self.fnt
        clr = self.textColor
        s = 17  # Space between lines
        lbls = []


        # Draw toolbar
        lbls.append((lambda pos: pygame.draw.rect(self.screen, (60, 60, 60), (pos[0], pos[1], screenWidth,
                                      self.toolbarHeight), 0), (0, screenHeight - self.toolbarHeight), 0))

        lblWid = gameWidth / 7
        # Draw toolbar stats
        x = gameWidth - lblWid * 3 - 15
        y = gameHeight + 15
        lbls.append((fnt.render(  "FPS:  " +                    str(self.fps), 5, clr), (x + lblWid * 0, y + s * 0), 0))
        lbls.append((fnt.render(  "Step: " +                str(self.frames) , 5, clr), (x + lblWid * 0, y + s * 1), 0))
        lbls.append((fnt.render("Critters: " + str(objects.getCount(Critter)), 5, clr), (x + lblWid * 1, y + s * 0), 0))
        lbls.append((fnt.render("FoodObjs: " +    str(objects.getCount(Food)), 5, clr), (x + lblWid * 1, y + s * 1), 0))
        lbls.append((fnt.render("Energy: " +  str(int(self.shared["energy"])), 5, clr), (x + lblWid * 2, y + s * 0), 0))
        lbls.append((fnt.render("Max:    "+str(int(self.shared["energyCap"])), 5, clr), (x + lblWid * 2, y + s * 1), 0))
        if self.selected is not None:
            obj = self.selected

            # Place the translucent gray box
            lbls.append(self.infoBox)

            # Draw a picture of the Critter
            lbls.append((lambda pos: pygame.draw.circle(self.screen, obj.attributes["color"], pos, int(obj.radius) + 3),
                         (gameWidth - self.infoBoxWidth / 2, gameHeight - self.infoBoxHeight + 40), 0))

            # Draw the health bar of the Critter
            x =  gameWidth -  self.infoBoxWidth + 10
            y = gameHeight - self.infoBoxHeight + 80

            def meterBar(x, y, w, h, curVal, maxVal):
                curVal = clamp(curVal, 0, maxVal)
                y += 5
                h -= 5
                lbls.append((lambda none: pygame.draw.rect(self.screen, (200,100,100),(x, y,  w, h), 0), 0, -1))
                lbls.append((lambda none: pygame.draw.rect(self.screen, (100,200,100),
                                                           (x, y, int(w * curVal/maxVal), h), 0), 0, -1))

            meterBar(gameWidth - 3 * self.infoBoxWidth/4, y - s, 2*self.infoBoxWidth / 4, s,
                     obj.health, obj.attributes["maxHealth"])

            # Create the Critter information Box
            lbls.append((fnt.render("Hunger:    "                                       , 5, clr), (x, y + s * 1), 0))
            meterBar(gameWidth - self.infoBoxWidth / 2, y + s*1, self.infoBoxWidth / 2 - 20, s, obj.hunger, 100)
            lbls.append((fnt.render("Fatigue:  "                                        , 5, clr), (x, y + s * 2), 0))
            meterBar(gameWidth - self.infoBoxWidth / 2, y + s*2, self.infoBoxWidth / 2 - 20, s, obj.sleepiness, 100)
            lbls.append((fnt.render("Aptitude: " +                  str(obj.personality), 5, clr), (x, y + s * 3), 0))
            lbls.append((fnt.render("Kills:    " +                        str(obj.kills), 5, clr), (x, y + s * 4), 0))
            lbls.append((fnt.render("Foods:    " +                    str(obj.foodEaten), 5, clr), (x, y + s * 5), 0))
            lbls.append((fnt.render("Mates:    " +                        str(obj.mates), 5, clr), (x, y + s * 6), 0))
            lbls.append((fnt.render("ID:       " +                           str(obj.ID), 5, clr), (x, y + s * 7), 0))
            lbls.append((fnt.render("State:    " +                        str(obj.state), 5, clr), (x, y + s * 8), 0))
            lbls.append((fnt.render("Age:      " +                          str(obj.age), 5, clr), (x, y + s * 9), 0))
            lbls.append((fnt.render("Gen:      " +     str(obj.attributes["generation"]), 5, clr), (x, y + s *10), 0))
            lbls.append((fnt.render("Family:   " + str(len(obj.attributes["relatives"])), 5, clr), (x, y + s *11), 0))
            lbls.append((fnt.render("Speed:    " +              str(round(obj.speed, 1)), 5, clr), (x, y + s *12), 0))
            lbls.append((fnt.render("    Gene #" + str(obj.genes.index(obj.curGene) + 1), 5, clr), (x, y + s *15), 0))
            lbls.append((fnt.render("IF        "                                        , 5, clr), (x, y + s *16), 0))
            lbls.append((fnt.render(str(obj.curGene["test"].__name__) + " " + str(obj.curGene["sign"]) + " " +
                                                         str(int(obj.curGene["thresh"])), 5, clr), (x, y + s *17), 0))
            lbls.append((fnt.render("THEN      "                                        , 5, clr), (x, y + s *18), 0))
            lbls.append((fnt.render(                 str(obj.curGene["action"].__name__), 5, clr), (x, y + s *19), 0))

            # lbls.append((fnt.render("Radius:     " +                  str(int(obj.radius)), 5, clr), (x, y + s *10), 0))

            lbls.append((lambda pos: pygame.draw.circle(self.screen, (255,0,0), pos, int(obj.radius) + 5, 5),
                             obj.intPos(obj.getPos()), -1))
            for id in obj.attributes["relatives"]:
                rel = objects.get(id)
                if rel is None: continue
                lbls.append((lambda args: pygame.draw.circle(self.screen, (255, 255, 255), args[0], args[1], 5),
                                                [rel.intPos(rel.getPos()), int(rel.radius) + 5], -1))

        self.rndr = self.rndr + lbls


    def handleEvents(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.VIDEORESIZE:
                global screenWidth, screenHeight, gameWidth, gameHeight

                screenWidth, screenHeight = event.size

                if screenWidth < self.minScreenWidth:   screenWidth = self.minScreenWidth
                if screenHeight < self.minScreenHeight: screenHeight = self.minScreenHeight

                self.screen   = pygame.display.set_mode((screenWidth, screenHeight), HWSURFACE|DOUBLEBUF|RESIZABLE)
                gameWidth, gameHeight = screenWidth, screenHeight - self.toolbarHeight
                self.initUI()
                self.renderScreen = True
                # Make sure that all food objects  are within the bounds of the world.
                for obj in objects:
                    if type(obj) is not Food: continue
                    if obj.pos[0] <            0: obj.pos[0] = 0
                    if obj.pos[1] <            0: obj.pos[1] = 0
                    if obj.pos[0] >  screenWidth: obj.pos[0] = screenWidth
                    if obj.pos[1] > screenHeight: obj.pos[1] = screenHeight

            self.updateKeys(event)
            self.gui.event(event)

    def updateKeys(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == K_r:
                keys["r"] = True
            elif event.key == pygame.K_e:
                keys["e"] = True
            elif event.key == pygame.K_p:
                keys["p"] = True
            elif event.key == pygame.K_n:
                keys["n"] = True

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_r:
                keys["r"] = False
            elif event.key == pygame.K_e:
                keys["e"] = False
            elif event.key == pygame.K_p:
                keys["p"] = False
            elif event.key == pygame.K_n:
                keys["n"] = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left Mouse
                keys["mouseL"] = True
            if event.button == 3:  # Right Mouse
                keys["mouseR"] = True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left Mouse
                keys["mouseL"] = False
            if event.button == 3:  # Right Mouse
                keys["mouseR"] = False

        keys["mousePos"] =  pygame.mouse.get_pos()

    def mouseLeft(self):
        if not keys["mouseL"]: return

        if self.mouseMode == "select":
            self.selected     = self.getClicked(Critter)
            self.selectedData = None
            if self.selected is not None:
                self.selected.printGenes()
                self.selectedData = self.selected.getSaveData()
            return


        if self.mouseMode == "critter":
            if self.selectedData is None:
                objects.add(Critter(objects.nextID, x=keys["mousePos"][0], y=keys["mousePos"][1]))
            else:
                newCritter = Critter(objects.nextID, x=keys["mousePos"][0], y=keys["mousePos"][1])
                newCritter.loadSaveData(self.selectedData)
                objects.add(newCritter)
            return

        if self.mouseMode == "food":
            objects.add(Food(objects.nextID, nutrition=100, x=keys["mousePos"][0], y=keys["mousePos"][1]))
            return

        if self.mouseMode == "wall":
            if self.getClickedGrid(Wall) is None:
                print "Placing wall"
                objects.add(Wall(objects.nextID, x=keys["mousePos"][0], y=keys["mousePos"][1]))
                return

        if self.mouseMode == "plant":
            if self.getClickedGrid(Plant) is None:
                print "Placing Plant"
                objects.add(Plant(objects.nextID, x=keys["mousePos"][0], y=keys["mousePos"][1]))
                return

    def mouseRight(self):
        if not keys["mouseR"]: return

        if self.mouseMode == "select":
            if self.selected is None:
                self.selected     = self.getClicked(Critter)
                if self.selected is not None:
                    self.selectedData = self.selected.getSaveData()
            if self.selected is not None:
                self.selected.setPos(keys["mousePos"][0], keys["mousePos"][1])
            return


        if self.mouseMode == "critter":
            # CHECK DELETE CRITTERS
            delCrit = self.getClicked(Critter, radius= 30)
            self.rndr.append((lambda pos: pygame.draw.circle(self.screen, (255,0,0), pos, 30, 5), keys["mousePos"], -1))
            if delCrit is not None: delCrit.kill()
            return

        if self.mouseMode == "food":
            # CHECK DELETE FOOD
            delFood = self.getClicked(Food, radius= 30)
            self.rndr.append((lambda pos: pygame.draw.circle(self.screen, (255,0,0), pos, 30, 5), keys["mousePos"], -1))
            if delFood is not None: objects.delete(delFood)
            return

        if self.mouseMode == "wall":
            self.rndr.append((lambda pos: pygame.draw.circle(self.screen, (255,0,0), pos, Wall.radius / 2, 5), keys["mousePos"], -1))

            # CHECK DELETE WALLS
            delWall = self.getNearestTo(Wall, keys["mousePos"])
            if delWall is not None:
                if (keys["mousePos"][0] - (delWall.pos[0] + Wall.radius / 2)) ** 2 + (keys["mousePos"][1] - (delWall.pos[1] + Wall.radius / 2)) ** 2 < Wall.radius ** 2:
                    objects.delete(delWall)
            return

        if self.mouseMode == "plant":
            self.rndr.append((lambda pos: pygame.draw.circle(self.screen, (255,0,0), pos, Wall.radius / 2, 5), keys["mousePos"], -1))

            # CHECK DELETE PLANTS
            delPlant = self.getNearestTo(Plant, keys["mousePos"])
            if delPlant is not None:
                if (keys["mousePos"][0] - (delPlant.pos[0] + Wall.radius / 2)) ** 2 + (keys["mousePos"][1] - (delPlant.pos[1] + Wall.radius / 2)) ** 2 < Wall.radius ** 2:
                    objects.delete(delPlant)
            return

    def btnPressed(self, arg):
        print "MainWindow.btnPressed(): ", arg
        if arg is not "render": self.renderScreen = True

        if arg == "cycleMode":
            if self.menuMode == "PLACE":
                self.menuMode = "FIND"
            elif self.menuMode == "FIND":
                self.menuMode = "BEST"
            elif self.menuMode == "BEST":
                self.menuMode = "PLACE"
            self.initUI()

        if arg == "best_oldest":
            if self.bestOfAll["age"] is not None:
                self.setSelected(self.bestOfAll["age"])
                self.mouseMode = "critter"
            return

        if arg == "best_lineage":
            if self.bestOfAll["lineage"] is not None:
                self.setSelected(self.bestOfAll["lineage"])
                self.mouseMode = "critter"
            return

        if arg == "best_mate":
            if self.bestOfAll["mate"] is not None:
                self.setSelected(self.bestOfAll["mate"])
                self.mouseMode = "critter"
            return

        if arg == "best_pred":
            if self.bestOfAll["pred"] is not None:
                self.setSelected(self.bestOfAll["pred"])
                self.mouseMode = "critter"
            return
        if arg == "best_scav":
            if self.bestOfAll["scav"] is not None:
                self.setSelected(self.bestOfAll["scav"])
                self.mouseMode = "critter"
            return

        if arg == "live_oldest":
            oldest = 0
            for obj in objects:
                if type(obj) is Critter and obj.age > oldest:
                    self.selected     = obj
                    oldest = obj.age
            if self.selected is not None: # If it's an empty screen
                self.selectedData = self.selected.getSaveData()
            self.mouseMode = "critter"
            return

        if arg == "live_lineage":
            longestGen = 0
            for obj in objects:
                if type(obj) is Critter and obj.attributes["generation"] > longestGen:
                    self.selected = obj
                    longestGen = obj.attributes["generation"]
            self.setSelected(self.selected)
            self.mouseMode = "critter"
            return

        if arg == "live_mate":
            mostMates = 0
            for obj in objects:
                if type(obj) is Critter and obj.mates > mostMates:
                    self.selected = obj
                    mostMates = obj.mates
            self.setSelected(self.selected)
            self.mouseMode = "critter"
            return

        if arg == "render":
            self.renderScreen = not self.renderScreen
            if not self.renderScreen: self.screen.fill((47, 141, 255))  # If it's false, clear the screen
            return

        if arg == "save" and self.selected is not None:
            if self.selected is None: return
            obj = self.selected
            saveData = self.selected.getSaveData()

            try:
                os.makedirs("Critter_Saves")
            except:
                # If directory already exists
                pass

            filename = "Critter_Saves\\" + getFileName(saveData["attributes"]["cumulativeGen"],
                                                               obj.age,
                                                               obj.mates,
                                                               obj.kills,
                                                               obj.foodEaten)

            with open(filename, 'w') as outfile:
                json.dump(saveData, outfile, sort_keys=True, indent=4, separators=(',', ': '))
            return

        if arg == "load":
            Tk().withdraw()               # we don't want a full GUI, so keep the root window from appearing
            filename = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
            if filename == '': return
            jsonData = open(filename).read()
            saveData = json.loads(jsonData)
            self.selectedData = saveData
            self.mouseMode = "critter"
            return
        self.mouseMode = arg

    def sliderChange(self, slider):
        if slider[1] == "energy_slider":
            self.shared["energyCap"] = slider[0].value
            print slider[0].value


    def getClicked(self, objType, radius=None):
        for obj in objects:
            if type(obj) is not objType: continue

            if radius is None:
                objRad = obj.radius**2
            else:
                objRad = radius ** 2

            if (keys["mousePos"][0] - obj.pos[0])**2 + (keys["mousePos"][1] - obj.pos[1])**2 <= objRad:
                return obj
        return None

    def getClickedGrid(self, objType):
        mx, my = keys["mousePos"]
        mx -= mx % objType.radius
        my -= my % objType.radius
        nearest = self.getNearestTo(objType, (mx, my))

        if nearest is not None:  #Check if there's not already an object there
            if not (int(mx) == int(nearest.pos[0]) and int(my) == int(nearest.pos[1])):
                return None  # Nothing clicked
        else:
            return None  # Nothing clicked
        return nearest

    def getNearestTo(self, objType, coords):
        closeObj = None
        minDist  = 10000000

        for obj in objects:
            if type(obj) is not objType: continue

            dist = (coords[0] - obj.pos[0])**2 + (coords[1] - obj.pos[1])**2
            if dist < minDist:
                minDist = dist
                closeObj = obj

        return closeObj

    def setSelected(self, obj):
        self.selected = obj
        if obj is not None:
            self.selectedData = obj.getSaveData()
        else:
            self.selectedData = None

class GameObjects:
    maxSearch = {Critter: 10, Food: 2, Wall: 10, Plant: 2}


    def __init__(self):

        self.objectDict = {}
        self.objCount = {}   # {type: #, type: #, type: #}
        self.kdTrees  = {}   # {Critter: (indexToID, critterKDTree), other types ... }
        self.nextID = 0      # Total number of objects that have ever been created

    def add(self, newObject):
        if self.getInGridObj(Wall, newObject):
            print "In wall!"
            return  # If object is spawning inside a wall

        if type(newObject) in self.objCount:
            self.objCount[type(newObject)] += 1
        else:
            self.objCount[type(newObject)] = 1

        if self.nextID in self.objectDict: print "ERROR ID REPEAT"
        self.objectDict[self.nextID] = newObject
        self.nextID += 1

    def get(self, ID):
        if not ID in self.objectDict: return None
        return self.objectDict[ID]


    def generateKDTree(self):
        """
        Generates a numpy array of [x,y]'s like [[x,y],[x,y],[x,y],[x,y]]
        At the same time, generates array of ID's corrosponding to the objects of those coords

        Example:
            Coord array: [[x,y],[x,y],[x,y],[x,y]]
            ID array:  : [    0,   23,   19, 1000]
        """

        # PROTOTYPE
        self.kdTrees = {}
        allCoords    = {}
        objCount     = {}

        self.indexToID = np.zeros((len(self.objectDict), 1))


        for key in self.objectDict:
            objType = type(self.objectDict[key])

            if objType not in self.kdTrees:
                self.kdTrees[objType] = [np.zeros((self.objCount[objType], 1)), None]
                allCoords[objType]    = np.zeros((self.objCount[objType], 2))
                objCount[objType]     = 0


            self.kdTrees[objType][0][objCount[objType]] = self.objectDict[key].ID
            allCoords[objType][objCount[objType]][0] = int(self.objectDict[key].pos[0])
            allCoords[objType][objCount[objType]][1] = int(self.objectDict[key].pos[1])
            objCount[objType] += 1

        for objType in self.kdTrees:
            self.kdTrees[objType][1] = cKDTree(allCoords[objType], leafsize=2)

    def getNeighborsSorted(self, id, objType):

        if id not in self.objectDict: return None


        distColumn, idColumn = self.kdTrees[objType][1].query(self.get(id).pos, k=self.maxSearch[objType])

        indexToID = self.kdTrees[objType][0]

        for i in range(0, idColumn.size):
            if distColumn[i] == float('inf'):
                idColumn = idColumn[:i]
                distColumn = distColumn[:i]
                break
            idColumn[i] = indexToID[idColumn[i]]


        return np.dstack([idColumn, distColumn])[0]

    def getInGridObj(self, objType, newObj, radius=None):

        nearest = None
        minDist  = 100000000
        for obj in objects:
            if type(obj) is not Wall: continue

            dist = (newObj.pos[0] - obj.pos[0] - obj.radius/2)**2 + (newObj.pos[1] - obj.pos[1] - obj.radius / 2)**2
            if dist < minDist:
                minDist = dist
                nearest = obj


        mx, my = newObj.pos
        mx    -= mx % objType.radius
        my    -= my % objType.radius

        if nearest is not None:  #Check if there's not already an object there
            if not (int(mx) == int(nearest.pos[0]) and int(my) == int(nearest.pos[1])):
                return False  # Nothing clicked
        else:
            return False  # The object doesn't even exist, so newObj can't be inside of it
        return True




    def getCount(self, objType):
        if objType in self.objCount:
            return self.objCount[objType]
        else:
            return 0

    def delete(self, object):

        if object.ID in self.objectDict:  # Make sure the object still exists
            self.objectDict.pop(object.ID)
            self.objCount[type(object)] -= 1


    def existsObj(self, object):
        return object.ID in self.objectDict

    def existsID(self, ID):
        return ID in self.objectDict

    def __iter__(self):
        return iter(self.objectDict.values())


def getFileName(gen, age, mates, kills, foods):
    # Critter_G#####__A#####__M###__K###__F###
    gen   = str(gen)
    age   = str(age)
    mates = str(mates)
    kills = str(kills)
    foods = str(foods)


    name   = "Critter_G" + gen   + "_" * (7 - len(gen))
    name  +=         "A" + age   + "_" * (7 - len(age))
    name  +=         "M" + mates + "_" * (5 - len(mates))
    name  +=         "K" + kills + "_" * (5 - len(kills))
    name  +=         "F" + foods + "_" * (5 - len(foods))
    name  += ".evo"

    return name


clamp = lambda n, minn, maxn: max(min(maxn, n), minn)

if __name__ == "__main__":
    global keys, screenWidth, screenHeight, gameWidth, gameHeight

    keys = {"e": False, "r": False, "p": False, "n": False, "mouseL": False, "mouseR": False, "mousePos": (0, 0)}
    screenWidth, screenHeight = 1000, 600
    gameWidth,     gameHeight = screenWidth, screenHeight - MainWindow.toolbarHeight
    objects = GameObjects()
    main = MainWindow()
    main.run()