class Action():
    def __init__(self,instName,actionType,actionData):
        self._actionType= actionType
        self._actionData = actionData
        self._instName = instName
    def __repr__(self):
        return(f'Instrument:{self._instName},Action Type:{self._actionType},Action Data:{self._actionData}')