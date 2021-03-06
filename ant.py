"""
Python implementation of Ant Colony Optimisation (ACO) meta-heuristic, for course requirements of CITS4404 @ University of Western Australia
"""
import random 
import math
import networkx as nx
import csv

"""
We can represent things differently now that we have are moving 
from the Moving Salesman to Vehicle Routing
What we need to represent: 
    - The routing graph (networkx object) [ACO Class]
        - The capacity of a vehicle (ant capactiy) [Ant Class]
    - The number of vehicles (num_ants) [ACO Class]
    - The unvisted nodes [ACO Class]
    - The number of iterations
    - {Optional} Maxmimum length travelled by an ant [Ant Class]
"""
        
class Ant(object): 

    def __init__(self,id, depot=(0,0),capacity=50):
        self._id = id
        self._solution = nx.DiGraph() # This is an empty graph
        self._depot = depot
        self._current = None
        self.capacity =  capacity
        self._max_capacity= capacity

        self._solution.add_node('depot')
        self._current='depot'

    def __repr__(self):
        return self._id

    def __str__(self):
        return str(self._id)

    def reset_capacity(self):
        self.capacity = self._max_capacity
    def get_solution(self):
        return self._solution.edges() 
    
    def update_solution(self, next_customer):
        # Initialise the graph and add the depot to it; this should always happen the first time.

        self._solution.add_node(next_customer)
        # print next_customer
        self._solution.add_edge(self._current,next_customer) 
        self._current = next_customer
        

    def get_current_position(self):
        return self._current

    def fitness_selection(self):
        return -1


class AntColony(object):
    def __init__(self,num_ants=5,alpha=0.5, beta=0.5,iteration=5,q_zero=0.8,graph_file=None):
        self._graph = None
        self._iteration = iteration
        self._ants = num_ants
        self._colony = []
        self._depot = (-1,0)
        self._graph_file = graph_file

        self._init_pheromone = 1/float(300)
        self._q0 = q_zero # most of the time, we use the pheromone
        self._alpha = alpha
        self._beta = beta
        self._unvisted_customers = None        
        self._best_solution = None
        self._best_solution_dist = -1

    def _init_ants(self):
        """
        This function initialises ants in the colony 
        """
        for x in range(0,self._ants):
            self._colony.append(Ant(x,self._depot,50))

        return self._colony

    def _init_graph(self, graph_file=None):
        """
        How the graph is constructed:
        graph = nx.Graph() initialises an empty graph
        graph.add_node(1) will add '1' to the graph
        For our purposes, we can also add other attributes
        graph.add_node(1,coord=(45,60),demand=17)
        We then access nodes and their coordinates like this: 
        >>  In[1]: graph.node[1]
        >> Out[1]: {'coord':(45,60), 'demand':17}
        """

        # TODO - Read in the graph from the CSV file

        # CONSTRUCT A TEMPORARY, SMALL GRAPH

        self._graph = nx.Graph()
        self._graph.add_nodes_from([1,2,3,4]) 
        coords = [(45,60),(-45,60),(45,-60),(-45,-60)]
        demand = [4,5,5,7]
        for x in range(1,5):
            self._graph.node[x]['coord']=coords[x-1]
            self._graph.node[x]['demand'] = demand[x-1]

        # The list of unvisited customers 
        self._unvisted_customers = list(self._graph.nodes())

        # Initialise all edges on the graph, set the pheromone to 0
        self._graph.add_node('depot')
        self._graph.node['depot']['coord']=self._depot
        for node in self._graph:
            for other_node in self._graph:
                if other_node is not node:
                    self._graph.add_edge(node,other_node,pheromone=5)


        return self._graph 


    def csv_parser(self, graph_file=None):
        """
        graph_file = file path
        its assumed that 1st row will be contianing labels
        in order : CUST, NO.XCOORD., YCOORD.,DEMAND, READY TIME, DUE DATE, SERVICE TIME
        """
        self._graph = nx.Graph()

        #Reading from CSV, fetching data
        data = []
        try:
            with open(graph_file, 'rb') as csvfile:
                csv_reader = csv.reader(csvfile, delimiter=',')

                for i in csv_reader:
                    if not i[1].isdigit():
                        continue
                    else:
                        try:
                            temp = {}
                            temp["x_cord"] = i[1]
                            temp["y_cord"] = i[2]
                            temp["customer_id"] = i[0]
                            temp["demand"] = i[3]
                            data.append(temp)
                        except Exception as err:
                            pass                
        except Exception as err:
            
            return -1

        for i in data:
            self._graph.add_node(i["customer_id"],coord=(int(i["x_cord"]),int(i["y_cord"])),demand=int(i["demand"]))
        
        #Here I am setting pheromone value to 5 as i not clear about the config/structure that we will follow 
        self._unvisted_customers = list(self._graph.nodes())        

        self._graph.add_node('depot')
        self._graph.node['depot']['coord']=self._depot

        for node in self._graph:
            for other_node in self._graph:
                if other_node is not node:
                    self._graph.add_edge(node,other_node,pheromone=self._init_pheromone)
        
        return self._graph




    def global_pheromone_update(self,edges,local_dist):
        """
        This function decays the pheromones on the trail
        """
        for edge in edges:
            if edge[0] is 'depot' and edge[1] is 'depot':
                continue
            edge_pheromone = self._graph[edge[0]][edge[1]]['pheromone']
            self._graph[edge[0]][edge[1]]['pheromone'] = (1-self._alpha)*edge_pheromone + self._alpha*local_dist
            # print self._graph[edge[0]][edge[1]]['pheromone']

        return 0

    def distance(self, c1, c2):
        """
        Calculate the distance between the coordinates of 2 vertices
        :param c1: The coordinate tuple of the first vertex
        :param c2: The coordinate tuple of the second vertex
        """

        c1x,c1y = c1
        c2x,c2y = c2

        dist = math.sqrt(pow((c1x-c2x),2) + pow((c1y-c2y),2))
        # print dist
        return int(dist)

    def pheromone_decay(self, edge):
        local_pheromone = self._graph[edge[0]][edge[1]]['pheromone'] 
        self._graph[edge[0]][edge[1]]['pheromone'] = (1-self._alpha)*local_pheromone + self._alpha*5
        # print self._graph[edge[0]][edge[1]]['pheromone']
        return 1

    def roullette_wheel(self,possible_customers,ant_pos,q):
        """
        Create a roulette wheel of unvisted cities
        Spin the wheel, then pick based on the probabilities
        """        
        # Possible customers is a list of customers we can serve

        total_dist = 0
        probabilities = dict()
        for customer in possible_customers:
            customer_coord = self._graph.node[customer]['coord']
            edge_pheromone = self._graph[ant_pos][customer]['pheromone']
            ant_coord = self._graph.node[ant_pos]['coord']
            dist = self.distance(ant_coord,customer_coord) 
            prob_formula = pow(edge_pheromone, self._alpha) * pow(1/float(dist), self._beta)
            total_dist = total_dist + prob_formula
            probabilities[customer] = prob_formula

        tmp = 0
        for customer in probabilities:
            probabilities[customer] = probabilities[customer]/total_dist + tmp
            tmp = probabilities[customer]
            if q < tmp:
                return customer

        return cust_probabilities
        
    def check_possible_customers(self,capacity):
        possible = []
        for customer in self._unvisted_customers:
            if self._graph.node[customer]['demand'] > capacity:
                continue 
            else: 
                possible.append(customer)

        return possible

    def reset_unvisted_customers(self):
        self._unvisted_customers = list(self._graph.nodes())
        self._unvisted_customers.remove('depot')

    def do_next_iteration(self):
        # print self._ants

        for ant in self._colony:   
            # print "Ant{0}".format(ant)
            self.reset_unvisted_customers()
            possible_customers = []
            best_customer = None
            next_ant = False
            # print unvisted_customers
            while len(self._unvisted_customers) > 0:

                possible_customers = self.check_possible_customers(ant.capacity)
                #Go back to the depot and refuel
                if not possible_customers:
                    ant.update_solution('depot')
                    ant.reset_capacity()
                    # A small part of me screams a little every time I see this, but we have safety nets below
                    possible_customers = self.check_possible_customers(ant.capacity)

                # We need to reset the max pheromone values and next customer for each iteration over possible customers
                next_customer = None
                max_pheromone = -1 

                for customer in possible_customers:
                    ant_pos = ant.get_current_position()
                    # print self._graph
                    edge_pheromone = self._graph[ant_pos][customer]['pheromone']
                    customer_coord = self._graph.node[customer]['coord']
                    ant_coord = self._graph.node[ant_pos]['coord']
                    dist = self.distance(ant_coord,customer_coord) 
                    q = random.random() 

                    if q < self._q0:
                        prob_formula = pow(edge_pheromone, self._alpha) * pow(1/float(dist), self._beta) 
                        if max_pheromone is -1:
                            max_pheromone = prob_formula
                            next_customer = customer
                        elif  max_pheromone < prob_formula:
                            max_pheromone = prob_formula
                            next_customer = customer 
                    else: 
                        # print "Lets play roulette instead!"
                        next_customer =self.roullette_wheel(possible_customers,ant.get_current_position(),q)

                ant.capacity = ant.capacity - self._graph.node[next_customer]['demand']
                ant.update_solution(next_customer)
                self._unvisted_customers.remove(next_customer)

                # print(self._unvisted_customers)
                # customer_count = customer_count + 1
                possible_customers = [] # Need to reset the possible customers too, other wise we keep adding to the same list!
                # print "we get here"
            
                if len(self._unvisted_customers) is 0:
                    # print "we never get here"
                    ant.update_solution('depot')
                    # print ant.get_solution()



                    
    def run(self):
        if not self._colony:
            self._init_ants()
            # print("Successfully initialised ants")
        if not self._graph:
            self.csv_parser('example_50.csv')
            # print("Successfully initialised graph")
        iteration_counter = 0
        while iteration_counter < self._iteration:
            # print self._graph.nodes()
            self.do_next_iteration()
            local_maxima = -1
            local_solution = []
            for ant in self._colony:
                edges = ant.get_solution()
                # print "ant solution" + str(edges)
                ant_dist = 0
                for edge in edges:  
                    c1 = self._graph.node[edge[0]]['coord']
                    c2 = self._graph.node[edge[1]]['coord']
                    ant_dist = ant_dist + self.distance(c1,c2)

                # print "ant dist:" + str(ant_dist)
                if local_maxima is -1:
                    local_maxima = ant_dist
                    local_solution = edges
                    # print ant_dist
                    # print("Local solution initialised for iteration {0}".format(iteration_counter))

                elif local_maxima > ant_dist:
                    local_maxima = ant_dist
                    local_solution = edges
                    # print("Best solution changed to ant {0}".format(ant))
                    # print(local_maxima)

            # Local pheromone decay
            for edge in self._graph.edges():
                self.pheromone_decay(edge)
                # print self._graph[edge[0]][edge[1]]['pheromone'] 

            
            
            for ant in self._colony:
                updateable_edges = []
                for edge in ant.get_solution():
                    if edge in local_solution:
                        updateable_edges.append(edge)
                # print updateable_edges
                self.global_pheromone_update(updateable_edges,local_maxima)    

            # for edge in self._graph.edges():
            #     print self._graph[edge[0]][edge[1]]['pheromone']
            # update the pheromones only on the local solution

            if self._best_solution_dist is -1:
                self._best_solution_dist = local_maxima
                self._best_solution = local_solution

            elif self._best_solution_dist > local_maxima:
                self._best_solution_dist = local_maxima
                self._best_solution = local_solution

            # Reset the colony and graphs (Kind of hack-y but c'est la vis)
            self._colony = []
            self._init_ants()

            self._graph = None
            self.csv_parser('example_50.csv')

            iteration_counter = iteration_counter + 1 

        # Itertions,Alpha,Beta,Customers, q0,Best Solution
        print("{4},{0},{1},{2},{5},{3}".format(self._alpha, self._beta, len(self._graph.nodes())-1, self._best_solution_dist,self._iteration,self._q0))
            
 





