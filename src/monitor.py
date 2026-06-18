from .models import Drone, Map

class Monitor:

    def __init__(self, game_map: Map):

        self.drones: list[Drone] = []
        self.map = game_map
        self.turn = 0    

    def init_drones(self):

        for i in range (self.map.nb_drones):
            path = self.map.hubs
            drone = Drone(i, self.map.start_hub, path)
            self.drones.append(drone)

    def next_turn(self):

        self.turn += 1
        for drone in self.drones:
            drone.current_hub = drone.path[self.turn]

