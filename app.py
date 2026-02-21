import streamlit as st
import math
import time
import matplotlib.pyplot as plt


class MRG32k3a:
    #MRG32k3a for random numbers
    def __init__(self, seed1=None, seed2=None):
        self.m1 = 4294967087.0
        self.a12, self.a13 = 1403580.0, -810728.0
        self.m2 = 4294944443.0
        self.a21, self.a23 = 527612.0, -1370589.0

        self.mrg_s1 = list(seed1 or [12345.0, 12346.0, 12347.0])
        self.mrg_s2 = list(seed2 or [12345.0, 12346.0, 12347.0])

    def next_random(self):
        #Update component 1
        p1 = (self.a12 * self.mrg_s1[1] + self.a13 * self.mrg_s1[0]) % self.m1
        self.mrg_s1 = [self.mrg_s1[1], self.mrg_s1[2], p1]

        #Update component 2
        p2 = (self.a21 * self.mrg_s2[2] + self.a23 * self.mrg_s2[0]) % self.m2
        self.mrg_s2 = [self.mrg_s2[1], self.mrg_s2[2], p2]

        z = p1 - p2
        if z < 0:
            z += self.m1

        return (z + 1.0) / (self.m1 + 1.0)

#Random Distributions

def normal(rng, mu=0, sigma=1):
    u1, u2 = rng.next_random(), rng.next_random()
    z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
    return mu + z * sigma

def exponential(rng, rate):
    u = rng.next_random() or 1e-10
    return -math.log(u) / rate

def gamma_tsang(rng, alpha, beta):
    if alpha < 1:
        return gamma_tsang(rng, alpha + 1, beta) * (rng.next_random() **(1/alpha))

    d = alpha - 1/3
    c = 1 / math.sqrt(9 * d)

    while True:
        z = normal(rng)
        if z <= -1/c:
            continue
        v = (1 + c * z)**3
        u = rng.next_random()
        if u < 1 - 0.0331 * z**4 or math.log(u) < 0.5 * z**2 + d * (1 - v + math.log(v)):
            return d * v * beta



# System Simulation

def simulate_one(rng, params):
    t_mission = params['mission_time']
    backup = params['use_backup']
    alpha, beta = params['main_alpha'], params['main_beta']
    lambda_d, lambda_a = params['lambda_dormant'], params['lambda_active']
    repair_mu, repair_sigma = params['repair_mu'], params['repair_sigma']

    t_main = gamma_tsang(rng, alpha, beta)

    if t_main > t_mission:
        return False, t_mission
    if not backup:
        return True, t_main

    t_dormant = exponential(rng, lambda_d)
    if t_dormant < t_main:
        return True, t_main

    repair_time = normal(rng, repair_mu, repair_sigma)
    active_time = exponential(rng, lambda_a)

    if t_main + repair_time < t_main + active_time:
        return False, t_mission
    if t_main + active_time < t_mission:
        return True, t_main + active_time
    return False, t_mission


def run_simulation(n_iter, params):
    rng = MRG32k3a()
    fails, times = [], []

    progress = st.progress(0)
    status = st.empty()
    start = time.time()

    for i in range(n_iter):
        fail, t = simulate_one(rng, params)
        fails.append(fail)
        times.append(t)

        if (i + 1) % max(1, n_iter//100)== 0:
            progress.progress((i + 1) / n_iter)
            status.text(f"Progress: {(i+1) * 100//n_iter}%")

    status.text(f"Simulation done in {time.time() - start:.2f}s")
    return fails, times


#Streamlit App
def main():
    st.set_page_config(page_title="Reliability Simulation", layout="wide")
    st.title("Stochastic Reliability Analysis")

    st.sidebar.header("Simulation Settings")
    mission_time = st.sidebar.number_input("Mission Time (Hours)", 200.0, step=10.0)
    use_backup = st.sidebar.checkbox("Enable Backup Generator", True)
    n_iter = st.sidebar.number_input("Iterations", 10000, step=1000, min_value=100)

    st.sidebar.subheader("Main Component (Gamma)")
    alpha = st.sidebar.number_input("Alpha (Shape)", 2.0, step=0.1)
    beta = st.sidebar.number_input("Beta (Scale)", 50.0, step=1.0)

    st.sidebar.subheader("Backup Component (Exponential)")
    lambda_a = st.sidebar.number_input("Lambda (Active)", 0.02, step=0.001, format="%.4f")
    lambda_d = st.sidebar.number_input("Lambda (Dormant)", 0.001, step=0.0001, format="%.4f")

    st.sidebar.subheader("Repair Process (Normal)")
    repair_mu = st.sidebar.number_input("Mean Repair Time", 10.0, step=1.0)
    repair_sigma = st.sidebar.number_input("Std Dev", 2.0, step=0.1)

    params = {
        'mission_time': mission_time,
        'use_backup': use_backup,
        'main_alpha': alpha,
        'main_beta': beta,
        'lambda_active': lambda_a,
        'lambda_dormant': lambda_d,
        'repair_mu': repair_mu,
        'repair_sigma': repair_sigma
    }

    if st.button("Run Simulation"):
        with st.spinner("Running Monte Carlo..."):
            fails, times = run_simulation(n_iter, params)
            total = len(fails)
            n_fail = sum(fails)
            pf = n_fail / total if total else 0
            margin = 1.96 * math.sqrt(pf * (1 - pf) / total) if total > 1 else 0

            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Failure Prob.", f"{pf:.4f}", f"{pf*100:.2f}%")
            col2.metric("Reliability", f"{1-pf:.4f}")
            col3.metric("95% CI", f"[{pf-margin:.4f}, {pf+margin:.4f}]")

            # Reliability plot
            sorted_times = sorted(times)
            unique_times = sorted(set(sorted_times))
            if unique_times and unique_times[0] > 0:
                unique_times.insert(0, 0.0)

            reliability = [sum(1 for x in sorted_times if x >= t)/total for t in unique_times]
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            ax1.plot(unique_times, reliability, color='#2E86C1', linewidth=2, label='Reliability')
            ax1.set_xlabel('Time (Hours)')
            ax1.set_ylabel('R(t)')
            ax1.set_title(f'Reliability Function (T={mission_time})')
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.legend()
            st.pyplot(fig1)

            #Convergence plot
            cum_fail = 0
            probs, iters = [], []
            step = max(1, total // 500)
            for i, f in enumerate(fails):
                if f:
                    cum_fail += 1
                if (i + 1) % step == 0:
                    probs.append(cum_fail / (i + 1))
                    iters.append(i + 1)

            fig2, ax2 = plt.subplots(figsize=(10, 6))
            ax2.plot(iters, probs, color='#C0392B', linewidth=1.5)
            ax2.axhline(y=pf, color='black', linestyle='--', alpha=0.5, label=f'Final Pf: {pf:.4f}')
            ax2.set_xlabel('Iterations')
            ax2.set_ylabel('Estimated Failure Probability')
            ax2.set_title('Monte Carlo Convergence')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            st.pyplot(fig2)


if __name__ == "__main__":
    main()