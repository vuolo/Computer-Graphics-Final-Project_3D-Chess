import numpy as np


class ObjLoader:
    def __init__(self, file):
        '''
        This Objloader class loads a mesh from an obj file.
        The mesh is made up of vertices.
        Each vertex is generally defined by the following attributes
             - position coordinates (v)
             - texture coordinates (vt)
             - normal coordinates (vn)

        There are other attributes that can be defined for a vertex,
        but we will not use them for now.

        Note: Sometimes, the obj file only contains position coordinates (v).

        If the obj file contains information for all three (v, vt, vn),
        then each vertex is made up of 8 floats:
                    3 for position coordinates  v = (x,y,z),
                    2 for texture coordinates   vt = (u,v),
                    3 for normals               vn = (xn,yn,zn)

        Important member variables to note:

        self.vertices:
            a one dimensional array of floats in the form:
            vertices = [ x,y,z, u,v, xn,yn,zn,    x,y,z, u,v, xn,yn,zn,   ...]
                        ------  ---   ------     ------  ---   ------
                        |  v     vt     vn |     | v     vt     vn  |
                        -------------------      -------------------    ...
                              vertex 1                vertex 2

        self.v:
            a list of vertex position coordinates
            v = [ [x,y,z], [x,y,z], [x,y,z], ...]

        self.vt:
            a list of vertex texture coordinates
            vt = [ [u,v], [u,v], [u,v], ...]

        self.vn:
            a list of vertex normal coordinates
            vn = [ [xn,yn,zn], [xn,yn,zn], [xn,yn,zn], ...]

        :param file:    full path to the obj file
        '''


        self.vertices = []      # 1D array of floats
        self.v = []             # list of vertex position coordinates
        self.vt = []            # list of vertex texture coordinates
        self.vn = []            # list of vertex normal coordinates

        self.load_mesh(file)

        self.center = None
        self.max = None
        self.min = None
        self.dia = None

        self.compute_model_extent(self.v)


        self.size_position = None
        self.size_texture = None
        self.size_normal = None
        self.itemsize = None
        self.stride = None
        self.offset_position = None
        self.offset_texture = None
        self.offset_normal = None
        self.n_vertices = None

        self.compute_properties_of_vertices()


    def load_mesh(self, filename):
        '''
        Load a mesh from an obj file.
        :param filename:
        :return:
        '''

        vertices = []

        with open(filename, "r") as file:
            for line in file:
                words = line.split()
                if len(words) == 0:
                    continue

                if words[0] == "v":
                    self.v.append(list(map(float, words[1:4])))
                elif words[0] == "vt":
                    self.vt.append(list(map(float, words[1:3])))
                elif words[0] == "vn":
                    self.vn.append(list(map(float, words[1:4])))
                elif words[0] == "f":
                    n_triangle = len(words) - 3

                    for i in range(n_triangle):
                        self.add_vertex(words[1], self.v, self.vt, self.vn, vertices)
                        self.add_vertex(words[2 + i], self.v, self.vt, self.vn, vertices)
                        self.add_vertex(words[3 + i], self.v, self.vt, self.vn, vertices)

        self.vertices = np.array(vertices, dtype=np.float32)
        self.v = np.array(self.v, dtype=np.float32)
        self.vt = np.array(self.vt, dtype=np.float32)
        self.vn = np.array(self.vn, dtype=np.float32)

    def add_vertex(self, corner_description: str,
                   v, vt,
                   vn, vertices) -> None:
        '''
        Add a vertex to the list of positions.
        :param corner_description:
        :param v:   list of vertex position coordinates
        :param vt:  list of vertex texture coordinates
        :param vn:  list of vertex normal coordinates
        :param vertices:
        :return:
        '''

        v_vt_vn = corner_description.split("/")
        v_vt_vn = list(filter(None, v_vt_vn))
        v_vt_vn = list(map(int, v_vt_vn))

        if len(v_vt_vn) == 1:
            vertices.extend(v[int(v_vt_vn[0]) - 1])
        elif len(v_vt_vn) == 2:
            if len(vn) == 0:
                vertices.extend(v[int(v_vt_vn[0]) - 1])     # add vertex coordinates to the list
                vertices.extend(vt[int(v_vt_vn[1]) - 1])    # add texture coordinates to the list
            elif len(vt) == 0:
                vertices.extend(v[int(v_vt_vn[0]) - 1])     # add vertex coordinates to the list
                vertices.extend(vn[int(v_vt_vn[1]) - 1])    # add normal coordinates to the list
        elif len(v_vt_vn) == 3:
            vertices.extend(v[int(v_vt_vn[0]) - 1])         # add vertex coordinates to the list
            vertices.extend(vt[int(v_vt_vn[1]) - 1])        # add texture coordinates to the list
            vertices.extend(vn[int(v_vt_vn[2]) - 1])        # add normal coordinates to the list



    def compute_model_extent(self, positions):
        '''
        Compute the model extent (min, max, center, diameter)
        :param positions:
        :return:
        '''
        self.min = np.array([np.inf, np.inf, np.inf])
        self.max = np.array([-np.inf, -np.inf, -np.inf])

        for v in positions:
            v = np.array(v)
            self.min = np.minimum(self.min, v)
            self.max = np.maximum(self.max, v)

        self.dia = np.linalg.norm(self.max - self.min)
        self.center = (self.min + self.max) / 2

        self.min = self.min.astype('float32')
        self.max = self.max.astype('float32')
        self.center = self.center.astype('float32')


    def compute_properties_of_vertices(self):
        '''
        Compute the properties of the vertices
        :return:
        '''
        self.size_position = self.v[0].size  # x, y, z
        self.size_texture = self.vt[0].size  # u, v
        self.size_normal = self.vn[0].size  # r, g, b

        self.itemsize = self.vertices.itemsize

        self.stride = (self.size_position + self.size_texture + self.size_normal) * self.itemsize
        self.offset_position = 0
        self.offset_texture = self.size_position * self.itemsize
        self.offset_normal = (self.size_position + self.size_texture) * self.itemsize
        self.n_vertices = len(self.vertices) // (
                    self.size_position + self.size_texture + self.size_normal)  # number of vertices



if __name__ == '__main__':
    '''
    This Objloader class loads a mesh from an obj file.
    The mesh is made up of vertices.
    Each vertex is generally defined by the following attributes
         - position coordinates (v)
         - texture coordinates (vt)
         - normal coordinates (vn)

    There are other attributes that can be defined for a vertex,
    but we will not use them for now.

    Note: Sometimes, the obj file only contains position coordinates (v).

    If the obj file contains information for all three (v, vt, vn),
    then each vertex will be made up of 8 floats:
                3 for position coordinates  v = (x,y,z),
                2 for texture coordinates   vt = (u,v),
                3 for normals               vn = (xn,yn,zn)

    Important member variables to note:

    self.vertices:
        a one dimensional array of floats in the form:
        vertices = [ x,y,z, u,v, xn,yn,zn,    x,y,z, u,v, xn,yn,zn,   ...]
                    ------  ---   ------     ------  ---   ------
                    |  v     vt     vn |     | v     vt     vn  |
                    -------------------      -------------------    
                          vertex 1                vertex 2          ...

    self.v:
        a list of vertex position coordinates
        v = [ [x,y,z], [x,y,z], [x,y,z], ...]

    self.vt:
        a list of vertex texture coordinates
        vt = [ [u,v], [u,v], [u,v], ...]

    self.vn:
        a list of vertex normal coordinates
        vn = [ [xn,yn,zn], [xn,yn,zn], [xn,yn,zn], ...]

    '''

    obj = ObjLoader("objects/raymanModel.obj")

    positions = obj.v
    print("Dimension of v: ", obj.v.shape)

    texture_coordinates = obj.vt
    print("Dimension of vt: ", obj.vt.shape)

    normal_coordinates = obj.vn
    print("Dimension of vn: ", obj.vn.shape)

    vertices = obj.vertices         # 1D array of vertices (position, texture, normal)
    print("Dimension of vertices: ", obj.vertices.shape)
