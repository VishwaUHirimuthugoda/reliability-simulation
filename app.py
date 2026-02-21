import streamlit as st
import math
import time
import matplotlib.pyplot as plt


class MRG32k3a:
    def __init__(self, seed1=None, seed2=None):
        #MRG32k3a Constants
        self.m1 = 4294967087.0
        self.a12 = 1403580.0
        self.a13 = -810728.0

        self.m2 = 4294944443.0
        self.a21 = 527612.0
        self.a23 = -1370589.0

        #Initial State
        if seed1 is None:
            self.mrg_s1 = [12345.0, 12346.0, 12347.0]
        else:
            self.mrg_s1 = list(seed1)
            
        if seed2 is None:
            self.mrg_s2 = [12345.0, 12346.0, 12347.0]
        else:
            self.mrg_s2 = list(seed2)

    def random_gen(self):
        #Component 1
        p1 = (self.a12 * self.mrg_s1[1] + self.a13 * self.mrg_s1[0]) % self.m1
        self.mrg_s1[0] = self.mrg_s1[1]
        self.mrg_s1[1] = self.mrg_s1[2]
        self.mrg_s1[2] = p1

        #Component 2
        p2 = (self.a21 * self.mrg_s2[2] + self.a23 * self.mrg_s2[0]) % self.m2
        self.mrg_s2[0] = self.mrg_s2[1]
        self.mrg_s2[1] = self.mrg_s2[2]
        self.mrg_s2[2] = p2

        #Combine both
        z = p1 - p2
        if z < 0:
            z += self.m1

        return (z + 1.0) / (self.m1 + 1.0)

#Statistical Distributions
def normal_box_muller(rng, mu, sigma):
    u1 = rng.random_gen()
    u2 = rng.random_gen()
    z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mu + z0 * sigma

def exponential(rng, lambd):
    u = rng.random_gen()
    if u == 0:
        u = 1e-10
    return -math.log(u) / lambd

def gamma_marsaglia_tsang(rng, alpha, beta):
    if alpha < 1:
        return gamma_marsaglia_tsang(rng, alpha + 1, beta) * (rng.random_gen() ** (1.0 / alpha))

    d = alpha - 1.0 / 3.0
    c = 1.0 / math.sqrt(9.0 * d)

    while True:
        z = normal_box_muller(rng, 0, 1)
        if z > -1.0 / c:
            v = (1.0 + c * z) ** 3
            u = rng.random_gen()

            if u < 1.0 - 0.0331 * (z**4):
                return d*v*beta

            if math.log(u) < 0.5 * (z**2) + d*(1.0 - v + math.log(v)):
                return d *v*beta


# Simulation Logic

def run_system_iteration(rng, params):
    #Unpack parameters
    mission_time = params['mission_time']
    use_backup = params['use_backup']
    main_alpha = params['main_alpha']
    main_beta = params['main_beta']
    lambda_dormant = params['lambda_dormant']
    lambda_active = params['lambda_active']
    repair_mu = params['repair_mu']
    repair_sigma = params['repair_sigma']

    #Main Component failure time
    t1 = gamma_marsaglia_tsang(rng, main_alpha, main_beta)

    if t1 > mission_time:
        return False, mission_time

    if not use_backup:
        return True, t1

    #Backup Dormant Failure Check
    t2_dormant = exponential(rng, lambda_dormant)
    if t2_dormant < t1:
        return True, t1
    
    #Attempt Repair of Main
    t_repair = normal_box_muller(rng, repair_mu, repair_sigma)
    
    #Backup Active Life
    t2_active = exponential(rng, lambda_active)
    time_repair_done = t1 + t_repair
    time_backup_fails = t1 + t2_active

    if time_repair_done < time_backup_fails:
        return False, mission_time
    else:
        if time_backup_fails < mission_time:
            return True, time_backup_fails
        else:
            return False, mission_time

def run_simulation(n_iterations, params):
    rng = MRG32k3a()
    results_failed = []
    results_time = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    start_time = time.time()
    
    for i in range(n_iterations):
        failed, t = run_system_iteration(rng, params)
        results_failed.append(failed)
        results_time.append(t)
        
        if (i + 1) % (n_iterations // 100) == 0:
            progress = (i + 1) / n_iterations
            progress_bar.progress(progress)
            status_text.text(f"Progress: {int(progress * 100)}%")

    elapsed = time.time() - start_time
    status_text.text(f"Simulation completed in {elapsed:.2f} seconds.")
    
    return results_failed, results_time

#Streamlit App UI

def main():
    st.set_page_config(page_title="Reliability Simulation", layout="wide")
    
    st.title("Stochastic Reliability Analysis of a Power System")
    st.markdown("""
    **Objective:** Simulate a power system (Main Grid, Backup Generator) over time.
    Model dynamic loads, component aging, random shocks, and repair cycles to calculate
    System Reliability R(t) and Availability A(t).
    """)

    #Sidebar Parameters
    st.sidebar.header("Simulation Parameters")
    
    #System Parameters
    st.sidebar.subheader("System Configuration")
    mission_time = st.sidebar.number_input("Mission Time (Hours)", value=200.0, step=10.0)
    use_backup = st.sidebar.checkbox("Use Backup Generator", value=True)
    n_iterations = st.sidebar.number_input("Number of Iterations", value=10000, step=1000, min_value=100)

    #Component Parameters
    st.sidebar.subheader("Main Component (Gamma Distribution )")
    main_alpha = st.sidebar.number_input("Alpha (Shape)", value=2.0, step=0.1)
    main_beta = st.sidebar.number_input("Beta (Scale)", value=50.0, step=1.0)
    
    st.sidebar.subheader("Backup Component (Exponential Distribution)")
    lambda_active = st.sidebar.number_input("Lambda (Active)", value=0.02, step=0.001, format="%.4f")
    lambda_dormant = st.sidebar.number_input("Lambda (Dormant)", value=0.001, step=0.0001, format="%.4f")
    
    st.sidebar.subheader("Repair Process (Normal Distribution)")
    repair_mu = st.sidebar.number_input("Mean Repair Time (Mu)", value=10.0, step=1.0)
    repair_sigma = st.sidebar.number_input("Repair Std Dev (Sigma)", value=2.0, step=0.1)

    params = {
        'mission_time': mission_time,
        'use_backup': use_backup,
        'main_alpha': main_alpha,
        'main_beta': main_beta,
        'lambda_active': lambda_active,
        'lambda_dormant': lambda_dormant,
        'repair_mu': repair_mu,
        'repair_sigma': repair_sigma
    }

    #Run Simulation
    if st.button("Run Simulation", type="primary"):
        with st.spinner("Running Monte Carlo Simulation..."):
            results_failed, results_time = run_simulation(n_iterations, params)
            
            #Results Calculation
            total = len(results_failed)
            failures = sum(results_failed)
            pf = failures / total if total > 0 else 0
            margin = 1.96 * math.sqrt((pf * (1 - pf)) / total) if total > 1 else 0.0
            
            #Display Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Failure Probability (Pf)", f"{pf:.4f}", f"{pf*100:.2f}%")
            col2.metric("Reliability (1-Pf)", f"{1-pf:.4f}")
            col3.metric("95% Confidence Interval", f"[{pf-margin:.4f}, {pf+margin:.4f}]")
            
            #Visualization
            st.markdown("### Reliability Analysis")
            tab1, tab2 = st.tabs(["Reliability Function R(t)", "Convergence Plot"])
            
            with tab1:
                #Reliability Curve
                sorted_times = sorted(results_time)
                unique_times = sorted(list(set(sorted_times)))
                if unique_times and unique_times[0] > 0:
                    unique_times.insert(0, 0.0)
                
                reliability = []
                for t in unique_times:
                    survivors = sum(1 for x in sorted_times if x >= t)
                    reliability.append(survivors / total)
                
                fig1, ax1 = plt.subplots(figsize=(10, 6))
                ax1.plot(unique_times, reliability, linewidth=2, color='#2E86C1', label='System Reliability')
                ax1.set_title(f'Reliability Function R(t) vs Time (T={mission_time})', fontsize=12)
                ax1.set_xlabel('Time (Hours)')
                ax1.set_ylabel('Reliability R(t)')
                ax1.grid(True, linestyle='--', alpha=0.7)
                ax1.legend()
                st.pyplot(fig1)

            with tab2:
                #Convergence Curve
                cumulative_failures = 0
                probs = []
                iterations = []
                step = max(1, total // 500) 
                
                for i, failed in enumerate(results_failed):
                    if failed:
                        cumulative_failures += 1
                    
                    if (i + 1) % step == 0:
                        probs.append(cumulative_failures / (i + 1))
                        iterations.append(i + 1)
                
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                ax2.plot(iterations, probs, color='#C0392B', linewidth=1.5)
                ax2.axhline(y=pf, color='black', linestyle='--', alpha=0.5, label=f'Final Prob: {pf:.4f}')
                ax2.set_title('Monte Carlo Convergence', fontsize=12)
                ax2.set_xlabel('Number of Iterations')
                ax2.set_ylabel('Estimated Failure Probability')
                ax2.grid(True, alpha=0.3)
                ax2.legend()
                st.pyplot(fig2)

if __name__ == "__main__":
    main()
