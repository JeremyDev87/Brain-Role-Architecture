# Dependency rules

Dependencies are explicit directed edges from a layer to the constraints or state it consumes. Every
dependency target must exist, self-dependency is forbidden, and the graph must be acyclic. Dependency
edges constrain compile order but anatomical responsibility names do not generate edges or order automatically.
