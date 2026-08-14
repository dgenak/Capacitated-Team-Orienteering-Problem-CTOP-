import random, copy
from Parser import load_model
import time
P1_SEEDS = 4
P2_SEEDS = 8
model = load_model("ctop_main_instance.txt")

K = model.vehicles
Q = model.capacity
T_MAX = model.t_max
N = model.num_nodes
DIST = model.cost_matrix
PROFITS = [node.profit for node in model.nodes]
DEMANDS = [node.demand for node in model.nodes]
MANDATORY = [node.isMandatory for node in model.nodes]
MAND_SET = set(int(i) for i in range(N) if MANDATORY[i] == 1)


# ΜΕΤΡΙΚΕΣ ΓΙΑ ΤΑ ΔΡΟΜΟΛΟΓΙΑ

# Υπολογίζει το συνολικό κόστος μιας διαδρομής
def cost(r):
    cost = 0.0
    for i in range(len(r) - 1):
        cost += DIST[r[i]][r[i+1]]
    return float(cost)
# Υπολογίζει το συνολικό φορτίο μιας διαδρομής
def load_per(r):
    demands_list = []
    for n in r:
        if n != 0:
            demand = DEMANDS[n]
            demands_list.append(demand)
    total_demand = sum(demands_list)
    result = int(total_demand)
    return result
# Υπολογίζει το συνολικό κέρδος μιας διαδρομής
def profit(r):
    profits_list = []
    for n in r:
        if n != 0:
            profit_value = PROFITS[n]
            profits_list.append(profit_value) 
    total_profit = sum(profits_list)
    result = int(total_profit) 
    return result

# Υπολογίζει το συνολικό κέρδος όλων των διαδρομών
def dro_profit(routes):
    profits_list = []
    for r in routes:
        route_profit = profit(r)
        profits_list.append(route_profit)
    total_profit = sum(profits_list)
    return total_profit

# ΕΛΕΓΧΟΣ ΕΓΚΥΡΟΤΗΤΑΣ ΔΡΟΜΟΛΟΓΙΩΝ
def einai_swsto(routes, mandatory_nodes=[], man=True):
    visited = []
    for r in routes:
        if not r or r[0] != 0 or r[-1] != 0:
            return False
        if cost(r) > T_MAX + 0.1:
            return False
        if load_per(r) > Q:
            return False
        for n in r:
            if n != 0:
                if n in visited:
                    return False
                visited.append(n)
    if man:
        all_mandatory_visited = True
        for node in mandatory_nodes:
            if node not in visited:
                all_mandatory_visited = False
                break
        if not all_mandatory_visited:
            return False
    return True

# μια 2-opt αντιστρέφει τμήματα της διαδρομής για να βρει καλύτερες διαδρομές στοχεύοντας στο μικρότερο κόστος
def two_opt(route):
    n = len(route)
    if (n <= 3):
        return route
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                a = route[i-1]
                b = route[i]
                c = route[j]
                d2 = route[j+1]
                current_cost = DIST[a][b] + DIST[c][d2]
                new_cost = DIST[a][c] + DIST[b][d2]
                cost_dif = current_cost - new_cost
                if cost_dif > 0.0001:
                    #παιρνουμε το τμήμα
                    sub_route = route[i:j+1]
                    #το αντιστρέφουμε
                    reversed_sub_route = sub_route[::-1]
                    # Αντικαθιστούμε το αρχικό τμήμα με το αντιστραμμένο
                    route[i:j+1] = reversed_sub_route
                    improved = True
    return route
# πανω κατω το ιδιο απλα το κάνει για όλες τις διαδρομές
def two_opt_all(routes):
    optimized_routes = []
    for r in routes:
        optimized_route = two_opt(r)
        optimized_routes.append(optimized_route)
    return optimized_routes

# Προσπαθεί να μετακινήσει ένα κόμβο από μια διαδρομή σε άλλη για μείωση κόστους
def or_opt(routes):
    improved = True
    while improved:
        improved = False
        # Υπολογίζουμε το φορτίο κάθε διαδρομής
        rl = []
        for r in routes:
            load = load_per(r)
            rl.append(load)
        # Υπολογίζουμε το κόστος κάθε διαδρομής
        rc = []
        for r in routes:
            route_cost = cost(r)
            rc.append(route_cost)

        for ri in range(K):
            #παιρνουμε την διαδρομή
            route = routes[ri]
            if len(route) <= 2:
                continue
            moved = False
            #για καθε κόμβο της διαδρομής
            for pos in range(1, len(route) - 1):
                node = route[pos]
                # Παίρνουμε τον προηγούμενο κόμβο
                p_n = route[pos - 1]
                # Παίρνουμε τον προηγούμενο κόμβο
                n_n = route[pos + 1]
                # Υπολογίζουμε το κέρδος από την αφαίρεση του κόμβου
                removal_gain = float(DIST[p_n][node] + DIST[node][n_n] - DIST[p_n][n_n])
                d = int(DEMANDS[node])
                # Αρχικοποιούμε τις μεταβλητές για την καλύτερη θέση
                best_g = 0.0001
                best_rj = -1
                best_p2 = -1
                # Επανάληψη για κάθε άλλη διαδρομήω
                for rj in range(K):
                    #παιρνουμε την διαδρομή που θα το βαλουμε
                    r2 = routes[rj]
                    #αν ειναι ιδια τότε ελεγχουμε για μετακίνηση εντός της ίδιας διαδρομής
                    if rj == ri:
                        new_rc = rc[ri] - removal_gain
                        for p2 in range(1, len(r2)):
                            # Αν η θέση είναι πολύ κοντά στην αρχική, παραλείπουμε γιατι δεν θα αλλάξει τίποτα ουσιαστικά
                            if abs(p2 - pos) <= 1:
                                continue
                            pa, pb = r2[p2-1], r2[p2]
                            if pa == node or pb == node:
                                continue
                            mesa = float(DIST[pa][node] + DIST[node][pb] - DIST[pa][pb])
                            # Ελέγχουμε αν το νέο κόστος δεν ξεπερνά το όριο
                            if new_rc + mesa <= T_MAX:
                                g = removal_gain - mesa
                                # Αν είναι καλύτερο, ενημερώνουμε τη καλύτερη θέση
                                if g > best_g:
                                    best_g = g
                                    best_rj = rj
                                    best_p2 = p2
                    #αν ειναι διαφορετικη
                    else:
                        if rl[rj] + d > Q:
                            continue
                        for p2 in range(1, len(r2)):
                            # Παίρνουμε τον προηγούμενο κόμβο στη νέα θέση
                            pa = r2[p2 - 1]
                            # Παίρνουμε τον επόμενο κόμβο στη νέα θέση
                            pb = r2[p2]
                            mesa = float(DIST[pa][node] + DIST[node][pb] - DIST[pa][pb])
                            # Ελέγχουμε αν το νέο κόστος δεν ξεπερνά το όριο
                            if rc[rj] + mesa <= T_MAX:
                                g = removal_gain - mesa
                                # Αν είναι καλύτερο, ενημερώνουμε τη καλύτερη θέση
                                if g > best_g:
                                    best_g = g
                                    best_rj = rj
                                    best_p2 = p2
                # Αν βρέθηκε καλύτερη θέση
                if best_rj >= 0:
                    # Αφαιρούμε τον κόμβο από την αρχική διαδρομή
                    new_route = []
                    for idx in range(len(route)):
                        # Παίρνουμε το στοιχείο στη θέση idx
                        x = route[idx]
                        # Προσθέτουμε το στοιχείο αν δεν είναι στη θέση pos
                        if idx != pos:
                            new_route.append(x)
                    # Ενημερώνουμε τη διαδρομή
                    routes[ri] = new_route
                    # Ενημερώνουμε τα κόστη
                    rc[ri] -= removal_gain
                    rl[ri] -= d
                    # Αν ο κόμβος παραμένει στην ίδια διαδρομή
                    if best_rj == ri:
                        # Υπολογίζουμε τη σωστή θέση
                        adj = best_p2 if best_p2 <= pos else best_p2 - 1
                        # Εισάγουμε τον κόμβο στη νέα θέση
                        routes[ri].insert(adj, node)
                        rc[ri] = cost(routes[ri])
                    
                    # αν ο κόμβος μετακινείται σε διαφορετική διαδρομή
                    else:
                        # Εισάγουμε τον κόμβο στη νέα θέση
                        routes[best_rj].insert(best_p2, node)
                        # Ενημερώνουμε το κόστος της νέας διαδρομής
                        rc[best_rj] = cost(routes[best_rj])
                        # Ενημερώνουμε το φορτίο της νέας διαδρομής
                        rl[best_rj] += d
                    improved = True
                    moved = True
                    break
            if moved:
                break
    return routes

# Αντικαθιστά κόμβους χαμηλού κέρδους με κόμβους υψηλού κέρδους που δεν έχουν επισκεφθεί
def money_is_everything(routes, mandatory_nodes=set()):
    improved = True
    while improved:
        improved = False
        # Υπολογίζουμε το φορτίο κάθε διαδρομής
        rl = []
        for r in routes:
            load = load_per(r)
            rl.append(load)
        # Υπολογίζουμε το κόστος κάθε διαδρομής
        rc = []
        for r in routes:
            route_cost = cost(r)
            rc.append(route_cost)
        # Βρίσκουμε όλους τους κόμβους που έχουν επισκεφθεί
        visited = set()
        for r in routes:
            for n in r:
                if n != 0:
                    visited.add(n)
        # Δημιουργούμε λίστα με τους κόμβους που δεν έχουν επισκεφθεί
        unvisited_list = []
        for i in range(1, N):
            if i not in visited:
                unvisited_list.append(i)
        # Ταξινομούμε τους κόμβους κατά κέρδος (μεγαλύτερο πρώτα)
        unvisited_all = sorted(
            unvisited_list,
            key=lambda x: PROFITS[x],
            reverse=True
        )

        for ri in range(K):
            r1 = routes[ri]
            # Δημιουργούμε λίστα με τους κόμβους που δεν είναι υποχρεωτικοί
            den = []
            for n in r1:
                if n != 0 and n not in mandatory_nodes:
                    den.append(n)
            
            # Αρχικοποιούμε τις μεταβλητές για την καλύτερη ανταλλαγή
            best_gain = -1
            best_n_out = -1
            best_n_in = -1
            best_pos_in = -1
            best_rj_in = -1
            best_tmp = None
            for n_out in den:
                # Βρίσκουμε τη θέση του κόμβου στη διαδρομή
                pos_out = r1.index(n_out)
                
                # Παίρνουμε τον προηγούμενο κόμβο
                pro = r1[pos_out - 1]
                
                # Παίρνουμε τον επόμενο κόμβο
                next = r1[pos_out + 1]
                # Υπολογίζουμε το κέρδος από την αφαίρεση του κόμβου
                rem_kerdos = float(DIST[pro][n_out] + DIST[n_out][next] - DIST[pro][next])
                # Παίρνουμε τη ζήτηση του κόμβου που αφαιρούμε
                d_out = int(DEMANDS[n_out])
                # Παίρνουμε το κέρδος του κόμβου που αφαιρούμε
                prof_out = int(PROFITS[n_out])
                #για καθε κομβο που θα εισαγουμε
                for n_in in unvisited_all:
                    prof_in = int(PROFITS[n_in])
                    gain = prof_in - prof_out
                    if gain <= best_gain:
                        break

                    d_in = int(DEMANDS[n_in])
                    # Ελέγχουμε αν μπορούμε να εισάγουμε τον κόμβο
                    if rl[ri] - d_out + d_in <= Q:
                        # Δημιουργούμε νέα διαδρομή
                        tmp = []
                        for x in r1:
                            if x != n_out:
                                tmp.append(x)
                        # Υπολογίζουμε το νέο κόστο
                        new_rc = rc[ri] - rem_kerdos
                        # Επανάληψη για κάθε δυνατή θέση εισαγωγής
                        for pos2 in range(1, len(tmp)):
                            pa, pb = tmp[pos2-1], tmp[pos2]
                            ins = float(DIST[pa][n_in] + DIST[n_in][pb] - DIST[pa][pb])



                            # Ελέγχουμε αν το νέο κόστος δεν ξεπερνά το όριο
                            if new_rc + ins <= T_MAX:
                                # Ελέγχουμε αν είναι καλύτερη ανταλλαγή
                                if gain > best_gain:
                                    # Ενημερώνουμε τη καλύτερη ανταλλαγή
                                    best_gain = gain
                                    best_n_out = n_out
                                    best_n_in = n_in
                                    best_pos_in = pos2
                                    best_rj_in = ri
                                    best_tmp = []
                                    for x in tmp:
                                        best_tmp.append(x)
                                break
                    for rj in range(K):
                        if rj == ri:
                            continue
                        if rl[rj] + d_in > Q:
                            continue
                        for pos2 in range(1, len(routes[rj])):
                            pa, pb = routes[rj][pos2-1], routes[rj][pos2]
                            ins = float(DIST[pa][n_in] + DIST[n_in][pb] - DIST[pa][pb])
                            # Ελέγχουμε αν το νέο κόστος δεν ξεπερνά το όριο
                            if rc[rj] + ins <= T_MAX:
                                # Ελέγχουμε αν είναι καλύτερη ανταλλαγή
                                if gain > best_gain:
                                    # Ενημερώνουμε τη καλύτερη ανταλλαγή
                                    best_gain = gain
                                    best_n_out = n_out
                                    best_n_in = n_in
                                    best_pos_in = pos2
                                    best_rj_in = rj
                                    best_tmp = None
                                break
            # Αν βρέθηκε καλύτερη ανταλλαγή

            if best_gain > 0:
                # Αφαιρούμε τον παλιό κόμβο και ενημερώνουμε φορτίο/κόστος
                new_route = []
                for x in routes[ri]:
                    if x != best_n_out:
                        new_route.append(x)
                routes[ri] = new_route
                rl[ri] -= int(DEMANDS[best_n_out])
                rc[ri] = cost(routes[ri])
                
                # Αν ο νέος κόμβος πάει στην ίδια διαδρομή
                if best_rj_in == ri:
                    routes[ri] = best_tmp
                    routes[ri].insert(best_pos_in, best_n_in)
                    rl[ri] += int(DEMANDS[best_n_in])
                    rc[ri] = cost(routes[ri])
                
                # Αν ο νέος κόμβος πάει σε άλλη διαδρομή
                else:
                    routes[best_rj_in].insert(best_pos_in, best_n_in)
                    rl[best_rj_in] += int(DEMANDS[best_n_in])
                    rc[best_rj_in] = cost(routes[best_rj_in])
                
                # Σημειώνουμε ότι έγιναν βελτιώσεις και σταματάμε
                improved = True
                break
    return routes

# Προσπαθεί να εισάγει κάθε κόμβο στη θέση με ελάχιστο κόστος
def greedy_insert_pool(routes, pool, mandatory_nodes=set()):
    # Βρίσκουμε όλους τους επισκεφθέντες κόμβους
    visited = set()
    for r in routes:
        for n in r:
            if n != 0:
                visited.add(n)
    
    # Βρίσκουμε τους κόμβους του pool που δεν έχουν επισκεφθεί
    monadikoi = []
    for n in pool:
        if n not in visited:
            monadikoi.append(n)
    
    # Ταξινομούμε τους κόμβους: πρώτα υποχρεωτικοί, μετά κατά κέρδος/ζήτηση
    profit_r = []
    for n in monadikoi:
        is_optional = n not in mandatory_nodes
        ratio = -PROFITS[n] / max(DEMANDS[n], 1)
        profit_r.append((is_optional, ratio, n))
    
    # ΚΡΙΣΙΜΟ: Ταξινομούμε ΜΟΝΟ κατά τα πρώτα 2 στοιχεία (χωρίς το n)
    # Έτσι έχουμε το ίδιο αποτέλεσμα με τη σύντομη έκδοση
    profit_r.sort(key=lambda x: x[:2])
    
    monadikoi = []
    for is_optional, ratio, n in profit_r:
        monadikoi.append(n)
    
    # Υπολογίζουμε το φορτίο κάθε διαδρομής
    rl = []
    for r in routes:
        load = load_per(r)
        rl.append(load)
    
    # Υπολογίζουμε το κόστος κάθε διαδρομής
    rc = []
    for r in routes:
        route_cost = cost(r)
        rc.append(route_cost)

    for node in monadikoi:
        # Αν ο κόμβος έχει ήδη επισκεφθεί, παραλείπουμε
        if node in visited:
            continue
        
        # Παίρνουμε τη ζήτηση του κόμβου
        d = int(DEMANDS[node])
        
        # Αρχικοποιούμε τις μεταβλητές για τη καλύτερη θέση
        best_delta = 99999
        best_r = -1
        best_p = -1
        
        for ri in range(K):
            # Αν ο κόμβος δεν χωράει στη διαδρομή, παραλείπουμε
            if rl[ri] + d > Q:
                continue
            
            route = routes[ri]
            for pos in range(1, len(route)):
                prev, nxt = route[pos-1], route[pos]
                # Υπολογίζουμε το κόστος εισαγωγής του κόμβου
                delta = float(DIST[prev][node] + DIST[node][nxt] - DIST[prev][nxt])
                # Ελέγχουμε αν το νέο κόστος δεν ξεπερνά το όριο και είναι καλύτερο
                if rc[ri] + delta <= T_MAX and delta < best_delta:
                    best_delta = delta
                    best_r = ri
                    best_p = pos
        
        # Αν βρέθηκε κατάλληλη θέση εισάγουμε τον κόμβο
        if best_r >= 0:
            routes[best_r].insert(best_p, node)
            rl[best_r] += d
            rc[best_r] += best_delta
            visited.add(node)
    
    return routes
# Κτίζει διαδρομές από την αρχή με greedy τρόπο για κάθε κόμβο (σε σειρά κέρδος/ζήτηση), τον εισάγει στη διαδρομή όπου κοστίζει λιγότερο
def greedy_build(priority_first=None):
    #φτιαχνουμε κενες διαδρομές
    routes = []
    for i in range(K):
        routes.append([0, 0])
    loads = [0] * K
    costs = [0.0] * K
    visited = set()
    
    if priority_first:
        # Δημιουργούμε σύνολο με τους υποχρεωτικούς κόμβους
        pset = set(priority_first)
        # Ταξινομούμε τους υποχρεωτικούς κόμβους κατά κέρδος/ζήτηση σε φθινουσα σειρα
        cands_priority = sorted(priority_first, key=lambda x: PROFITS[x]/max(DEMANDS[x],1), reverse=True)
        # Ταξινομούμε τους μη υποχρεωτικούς κόμβους κατά κέρδος/ζήτηση σε φθινουσα σειρα
        cands_other = sorted([i for i in range(1, N) if i not in pset],
                             key=lambda x: PROFITS[x]/max(DEMANDS[x],1), reverse=True)
        # Συνδυάζουμε τις δύο λίστες
        cands = cands_priority + cands_other
    else:
        cands = sorted(range(1, N), key=lambda x: PROFITS[x]/max(DEMANDS[x],1), reverse=True)
    
    # εισάγουμε κάθε κόμβο στη καλύτερη διαδρομή
    for node in cands:
        if node in visited:
            continue
        d = int(DEMANDS[node])
        best_delta =999999
        best_r = -1
        best_p = -1
        
        # Δοκιμάζουμε σε κάθε διαδρομή
        for ri in range(K):
            if loads[ri] + d > Q:
                continue
            route = routes[ri]
            rc = costs[ri]
            for pos in range(1, len(route)):
                prev = route[pos - 1]
                nxt = route[pos]
                delta = float(DIST[prev][node] + DIST[node][nxt] - DIST[prev][nxt])
                if rc + delta <= T_MAX and delta < best_delta:
                    best_delta = delta
                    best_r = ri
                    best_p = pos
        
        # Εισάγουμε τον κόμβο στη καλύτερη θέση
        if best_r >= 0:
            routes[best_r].insert(best_p, node)
            loads[best_r] += d
            costs[best_r] += best_delta
            visited.add(node)
    
    return routes

# ενα LS με 2opt, or-opt, profit_swap και μετά ξανα greedy insert για να βάλει κόμβους που δεν έχουν επισκεφθεί, με προτεραιότητα τους υποχρεωτικούς αν υπάρχουν
def local_search(routes, priority_first=None, mandatory_nodes=set()):
    routes = two_opt_all(routes)
    routes = or_opt(routes)
    routes = money_is_everything(routes, mandatory_nodes)
    # Βρίσκουμε τους κόμβους που δεν έχουν επισκεφθεί
    visited = set(n for r in routes for n in r if n != 0)
    unvisited = sorted([i for i in range(1, N) if i not in visited],
                       key=lambda x: PROFITS[x]/max(DEMANDS[x],1), reverse=True)
    # Αν υπάρχουν υποχρεωτικοί κόμβοι, τους προτιμάμε
    if priority_first:
        pset = set(priority_first)
        unvisited.sort(key=lambda x: (x not in pset, -PROFITS[x]/max(DEMANDS[x],1)))
    routes = greedy_insert_pool(routes, unvisited, mandatory_nodes)
    routes = two_opt_all(routes)
    return routes

# Διαταράσσει τις διαδρομές αφαιρώντας τυχαίους κόμβους και επανεισάγοντάς τους
def perturb(routes, mandatory_nodes=set(), n_remove=0):
    # αντιγράφουμε τα δεομολογια
    routes = copy.deepcopy(routes)
    # Βρίσκουμε όλους τους κόμβους που μπορούν να αφαιρεθούν (δεν είναι υποχρεωτικοί)
    removable = []
    for ri in range(len(routes)):
        route = routes[ri]
        for node in route:
            if node != 0 and node not in mandatory_nodes:
                removable.append((ri, node))

    # Βρίσκουμε πόσα items είναι διαθέσιμα προς αφαίρεση
    num_removable = len(removable)
    # Επιλέγουμε το μικρότερο είτε n_remove είτε τα διαθέσιμα items
    num_to_remove = min(n_remove, num_removable)
    # Επιλέγουμε τυχαίως αυτόν τον αριθμό κόμβων
    to_remove = random.sample(removable, num_to_remove)
    
    # Αφαιρούμε τους κόμβους από τις διαδρομές
    removed = []
    for ri, node in to_remove:
        if node in routes[ri]:
            routes[ri].remove(node)
            removed.append(node)
    
    # Ταξινομούμε τους αφαιρεμένους κόμβους κατά κέρδος σε αυξουσα
    removed.sort(key=lambda x: PROFITS[x], reverse=True)
    
    # Επανεισάγουμε τους αφαιρεμένους κόμβους στις καλύτερες θέσεις
    routes = greedy_insert_pool(routes, removed, mandatory_nodes)
    
    return routes

# Καταστρέφει και επανακατασκευάζει μέρος των διαδρομών για να βρει καλύτερες λύσεις
# Σε κάθε επανάληψη αφαιρούμε κόμβους επανεισάγοντάς τους καλύτερους και εφαρμόζουμε local search
def LNS(routes_init, max_iters=500, mandatory_nodes=set(), seed=42):
    random.seed(seed)
    best = copy.deepcopy(routes_init)
    best_p = dro_profit(best)
    current = copy.deepcopy(best)
    itr = 0
    pf = sorted(mandatory_nodes) if mandatory_nodes else None
    
    while itr < max_iters:
        itr += 1
        ypo = copy.deepcopy(current)
        
        # Υπολογίζουμε το ratio κέρδος/κόστος για κάθε διαδρομή
        scores = []
        for ri in range(len(ypo)):
            route = ypo[ri]
            route_profit = profit(route)
            route_cost = cost(route)
            ratio = route_profit / max(route_cost, 1)
            scores.append((ratio, ri))
        scores.sort()
        
        # Αφαιρούμε κόμβους από τις χειρότερες διαδρομές
        pool = []
        n_destroy = random.randint(1, 2)
        for i in range(n_destroy):
            ratio, ri = scores[i]
            nodes = []
            for n in ypo[ri]:
                if n != 0 and n not in mandatory_nodes:
                    nodes.append(n)
            for n in nodes:
                ypo[ri].remove(n)
                pool.append(n)
            if len(ypo[ri]) < 2:
                ypo[ri] = [0, 0]
        
        # Αφαιρούμε επιπλέον κόμβους χαμηλού κέρδους
        all_removable = []
        for ri in range(len(ypo)):
            for n in ypo[ri]:
                if n != 0 and n not in mandatory_nodes:
                    all_removable.append((ri, n))
        removable_with_ratio = []
        for ri, n in all_removable:
            ratio = PROFITS[n] / max(DEMANDS[n], 1)
            removable_with_ratio.append((ratio, ri, n))
        removable_with_ratio.sort()
        n_extra = random.randint(5, 20)
        for i in range(min(n_extra, len(removable_with_ratio))):
            ratio, ri, node = removable_with_ratio[i]
            if node in ypo[ri]:
                ypo[ri].remove(node)
                pool.append(node)
        
        # Προσθέτουμε τους κορυφαίους unvisited κόμβους
        visited_now = set()
        for r in ypo:
            for n in r:
                if n != 0:
                    visited_now.add(n)
        unvisited_all = []
        for i in range(1, N):
            if i not in visited_now:
                unvisited_all.append(i)
        kal = []
        for n in unvisited_all:
            ratio = PROFITS[n] / max(DEMANDS[n], 1)
            kal.append((ratio, n))
        kal.sort(reverse=True)
        unvisited_high = []
        for i in range(min(80, len(kal))):
            ratio, n = kal[i]
            unvisited_high.append(n)
        
        # Συνδυάζουμε και επανεισάγουμε τους κόμβους
        oloi = list(set(pool + unvisited_high))
        ypo = greedy_insert_pool(ypo, oloi, mandatory_nodes)
        ypo = local_search(ypo, pf, mandatory_nodes)
        
        # Ελέγχουμε την εγκυρότητα
        swsto = einai_swsto(ypo, mandatory_nodes, bool(mandatory_nodes))
        if not swsto:
            continue
        
        # Αποδεχόμαστε ή απορρίπτουμε τη λύση
        cp = dro_profit(ypo)
        current_p = dro_profit(current)
        if cp >= current_p:
            current = ypo
            if cp > best_p:
                best = copy.deepcopy(ypo)
                best_p = cp
                print(f"  LNS seed={seed} [Iter {itr}] profit={best_p}")
        else:
            random_value = random.random()
            if random_value < 0.05:
                current = ypo
    
    return best, best_p

# καταστρέφει και βελτιστοποιεί επαναληπτικά
def ILS_seed(routes_init, max_iters=300, mandatory_nodes=set(), priority_first=None, seed=42):
    random.seed(seed)
    pf = priority_first
    
    # Αρχικοποιούμε τις διαδρομές με local search
    routes = copy.deepcopy(routes_init)
    routes = local_search(routes, pf, mandatory_nodes)
    
    # Αρχικοποιούμε τη καλύτερη και τρέχουσα λύση
    best = copy.deepcopy(routes)
    best_p = dro_profit(routes)
    current = copy.deepcopy(routes)
    n_rem = 8
    no_improve = 0
    itr = 0
    
    while itr < max_iters:
        itr += 1
        
        # Διαταράσσουμε τις διαδρομές
        new_r = perturb(current, mandatory_nodes, n_rem)
        
        # Εφαρμόζουμε local search
        new_r = local_search(new_r, pf, mandatory_nodes)
        
        # Υπολογίζουμε το κέρδος της νέας λύσης
        np2 = dro_profit(new_r)
        current_p = dro_profit(current)
        
        # Αν είναι καλύτερη, κρατάμε τη λύση
        if np2 > current_p:
            current = new_r
            no_improve = 0
            
            # Αν είναι καλύτερη από τη best, ενημερώνουμε τη best
            if np2 > best_p:
                best = copy.deepcopy(new_r)
                best_p = np2
                print(f"  seed={seed} ILS profit={best_p} (Iter {itr})")
        
        # Αν δεν υπάρχει βελτίωση
        else:
            no_improve += 1
            
            # Αν δεν υπάρχει βελτίωση για 20 επαναλήψεις, ξαναρχίζουμε
            if no_improve >= 20:
                current = copy.deepcopy(routes)
                n_rem = random.randint(6, 15)
                no_improve = 0
    
    return best, best_p

#απλα για να γραφει τη λύση 

def write_solution(routes, path):
    with open(path, 'w') as f:
        for r in routes:
            f.write(' '.join(map(str, r)) + '\n')





# να σημειωθεί πως οι επιλογές των seeds, iterations και ααλλων παραμέτρων έγιναν μετά από αρκετές 
# δοκιμές για να βρεθεί η καλύτερη δυνατή λύση εντός του χρονικού ορίου




# ΛΥΣΗ NO MANDATORY

print("\n" + "="*60)
print("PROBLEM 1: Standard CTOP (no mandatory)")
print("="*60)
start_p1 = time.time()
# Αρχικοποιούμε τις μεταβλητές για το καλύτερο αποτέλεσμα
no_man_best_sol = 0
r1_best = None
seed = P1_SEEDS

random.seed(seed)

# Κατασκευάζουμε αρχική λύση και εφαρμόζουμε local search
r = greedy_build()
r = local_search(r, None, set())
p = dro_profit(r)

# Αν είναι καλύτερη, κρατάμε τη λύση
if p > no_man_best_sol:
    no_man_best_sol = p
    r1_best = copy.deepcopy(r)
    p1_best_seed = seed

# Εφαρμόζουμε ILS για περαιτέρω βελτίωση
r_new, p_new = ILS_seed(r, max_iters=100, mandatory_nodes=set(), seed=seed)

if p_new > no_man_best_sol:
    no_man_best_sol = p_new
    r1_best = r_new
    p1_best_seed = seed

print(f"After ILS: P1={no_man_best_sol} (best seed: {p1_best_seed})")

# Εφαρμόζουμε LNS για τελική βελτίωση

r_new, p_new = LNS(r1_best, max_iters=100, mandatory_nodes=set(), seed=seed)

is_valid_result = einai_swsto(r_new, set(), False)
if is_valid_result and p_new > no_man_best_sol:
    no_man_best_sol = p_new
    r1_best = r_new
    p1_best_seed = seed
    print(f"  LNS profit updated: {no_man_best_sol} (seed: {seed})")
end_p1 = time.time()

# Αποθηκεύουμε τη λύση
write_solution(r1_best, 'solution_no_mandatory.txt')


# ΛΥΣΗ MANDATORY
print("\n" + "="*60)
print("ΛΥΣΗ Mandatory CTOP")
print("="*60)

# Αρχικοποιούμε τις μεταβλητές για το καλύτερο αποτέλεσμα
p2_best = 0
r2_best = None
seed2 = P2_SEEDS
pf = sorted(MAND_SET)

random.seed(seed2)
time_p1 = end_p1 - start_p1
# Κατασκευάζουμε αρχική λύση με προτεραιότητα τους υποχρεωτικούς κόμβους
r = greedy_build(priority_first=pf)
r = local_search(r, pf, MAND_SET)
p = dro_profit(r)

# Ελέγχουμε την εγκυρότητα και κρατάμε αν είναι καλύτερη
is_valid_result = einai_swsto(r, MAND_SET, True)
if is_valid_result and p > p2_best:
    p2_best = p
    r2_best = copy.deepcopy(r)
    p2_best_seed = seed2


r_new, p_new = ILS_seed(r, max_iters=2400, mandatory_nodes=MAND_SET, priority_first=pf, seed=seed2)

is_valid_result = einai_swsto(r_new, MAND_SET, True)
if is_valid_result and p_new > p2_best:
    p2_best = p_new
    r2_best = r_new
    p2_best_seed = seed2

print(f"After ILS: P2={p2_best} (best seed: {p2_best_seed})")

# Εφαρμόζουμε LNS για τελική βελτίωση

r_new, p_new = LNS(r2_best, max_iters=200, mandatory_nodes=MAND_SET, seed=seed2)

is_valid_result = einai_swsto(r_new, MAND_SET, True)
if is_valid_result and p_new > p2_best:
    p2_best = p_new
    r2_best = r_new
    p2_best_seed = seed2
    print(f"  LNS P2 updated: {p2_best} (seed: {seed2})")
end_p2 = time.time()
time_p2 = end_p2 - start_p1
# Αποθηκεύουμε τη λύση
write_solution(r2_best, 'solution_mandatory.txt')

print("\n" + "="*70)
print("FINAL SOLUTION")
print("GKENAKOS - GAZON - DEMOPOULOS")
print("8230029 - 8230028 - 8230030")
print("="*70)
print(f"  No mandatory profit: {no_man_best_sol} (seed: {seed})")
print(f"  Mandatory profit: {p2_best} (seed: {seed2})")
print(f"  Solutions saved: solution_no_mandatory.txt, solution_mandatory.txt")
print(f"  Time taken - No mandatory: {time_p1:.2f} Seconds")
print(f"  Time taken - Mandatory: {time_p2:.2f} Seconds")
print("="*70)