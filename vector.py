#!/usr/bin/env python3

class Vector:
    
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    
    def __repr__(self):
        return f"v({self.x},{self.y},{self.z})"
    
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, other):
        assert type(other) == int
        return Vector(self.x * other, self.y * other, self.z * other)
    
    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self
    
    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self
    
    def __neg__(self):
        return Vector(-self.x, -self.y, -self.z)
    
    def copy(self):
        return Vector(self.x, self.y, self.z)
    
    # rotate 90° along the y axis, in + or - direction
    def rotate(self, positive_direction=True):
        dir = 1 if positive_direction else -1
        # +x -> -z , +z -> +x if pos dir
        # +x -> +z , +z -> -x if neg dir
        temp = self.x
        self.x = dir * self.z
        self.z = -dir * temp
    
    def rotated(self, positive_direction=True):
        v = self.copy()
        v.rotate(positive_direction=positive_direction)
        return v
    
    # direction is a vector with 2 coordinates being 0 and the 3rd one being +-1
    def get_coord(self, direction):
        return self.x * direction.x + self.y * direction.y + self.z * direction.z
