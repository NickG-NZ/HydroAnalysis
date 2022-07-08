"""
Results logging system for VPP
"""
import copy


class LogObject:
    """
    Data wrapper so that primitive types can be logged.
    Can't hold pointer to primitives in python, only objects.
    """


class Logger:

    class ChannelGroup:
        def __init__(self, name, obj):
            self.name = name
            self._obj = obj
            self._channels = {}
            self.aliases = {}

        def add_channel(self, channel_name, alias=None):
            """
            Note: since python doesn't provide a means of holding a consistent memory address
            the exact name must be provided for the member of 'obj'
            """
            if alias is None:
                alias = channel_name
            self.aliases[alias] = channel_name

            if alias in self._channels.keys():
                raise KeyError(f"LogGroup {self.name} already contains a channel called {alias}")
            if not hasattr(self._obj, channel_name):
                raise KeyError(f"ChannelGroup reference object: {self._obj} has no attribute {channel_name}")
            self._channels[alias] = []

        def get_channel_data(self, channel_alias):
            return self._channels[channel_alias]

        def log_channels(self):
            for alias, data in self._channels.items():
                data.append(copy.copy(getattr(self._obj, self.aliases[alias])))

    def __init__(self, log_name=""):
        self._log_name = log_name
        self._log_groups = {}
        self._running = False

    def run(self):
        """
        This just stops more channels being added after data has already been logged.
        Otherwise, alignment needs to be accounted for.
        """
        self._running = True

    def add_group(self, name, obj):
        """
        Have to pass in the object containing the primitive to be logged since
        python doesn't allow holding a const pointer to a primitive
        """
        if self._running:
            print("ERROR - Cannot add group after result logging has started")
        if name in self._log_groups.keys():
            return
        self._log_groups[name] = Logger.ChannelGroup(name, obj)

    def add_group2(self, group):
        """
        If the user has created their own ChannelGroup, they can pass it in directly
        """
        if self._running:
            print("ERROR - Cannot add group after result logging has started")
        if group.name in self._log_groups.keys():
            raise KeyError(f"A ChannelGroup called '{group.name}' already exists in the Logger")
        self._log_groups[group.name] = group

    def add_channel_to_group(self, channel_name, group_name, alias=None):
        """
        Each channel can be given an alias, rather than using the raw attribute name from
        the owning object
        """
        if self._running:
            print("ERROR - Cannot add channel to group after result logging has started")
        if "." in channel_name:
            raise ValueError("Channel name cannot contain periods '.'")
        if group_name not in self._log_groups.keys():
            raise KeyError(f"Non-existant group_name: {group_name}")
        self._log_groups[group_name].add_channel(channel_name, alias)

    def get_channel_log(self, group_name, channel_alias):
        return self._log_groups[group_name].get_channel_data(channel_alias)

    def get_group(self, group_name):
        return self._log_groups[group_name]

    def log_all(self):
        if not self._running:
            self.run()
        for group_name, group in self._log_groups.items():
            group.log_channels()

    def print_channel_aliases(self, group_name):
        print(f"\nGroup {group_name} channel aliases:")
        for alias, channel_name in self._log_groups[group_name].aliases.items():
            print(f"Alias: {alias} -> Channel: {channel_name}")


