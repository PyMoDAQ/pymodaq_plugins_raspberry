# Initializing an empty list

import numpy as np

list_of_lists = []

data = [5,4,3,3,45,4,6,7,8,1,2,3,4,5,2,44,33,2,1,32]
# Appending lists to create a list of lists
list_of_lists.append([1, 2, 3])
list_of_lists.append([4, 5, 6])
list_of_lists.append([7, 8, 9])

king = np.array(list_of_lists)

# Displaying the resulting list of lists
print(np.array(list_of_lists))


def get_data(list_signal, samples, nb_channel_activated):
    list_signal_arranged = []
    for k in range(nb_channel_activated):
        list_signal_arranged.append(np.array([list_signal[k]]))
    i = nb_channel_activated
    while i <= len(list_signal) - nb_channel_activated:
        for j in range(nb_channel_activated):
            list_signal_arranged[j] = np.append(list_signal_arranged[j], list_signal[i + j])
        i = i + nb_channel_activated
    return list_signal_arranged

gun  = get_data(data, 10, 2)
print(gun)