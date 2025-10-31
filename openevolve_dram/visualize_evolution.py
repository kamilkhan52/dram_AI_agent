#!/usr/bin/env python3
"""
Custom visualization tools for OpenEvolve DRAM optimization results.
Creates interactive plots showing the evolution process.
"""

import sqlite3
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def load_evolution_data(db_path='openevolve_output/database/map_elites.db'):
    """Load all programs and their metrics from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all programs with their metrics
    cursor.execute("""
        SELECT id, generation, island_id, parent_id, score, 
               code, metrics, features
        FROM programs
        ORDER BY generation, id
    """)
    
    programs = []
    for row in cursor.fetchall():
        prog = {
            'id': row[0],
            'generation': row[1],
            'island_id': row[2],
            'parent_id': row[3],
            'score': row[4],
            'code': row[5],
            'metrics': json.loads(row[6]) if row[6] else {},
            'features': json.loads(row[7]) if row[7] else {}
        }
        programs.append(prog)
    
    conn.close()
    return programs

def extract_parameters(code):
    """Extract CL, tRCD, tRP, tRAS from program code."""
    params = {}
    for line in code.split('\n'):
        if 'self.CL' in line and '=' in line:
            params['CL'] = int(line.split('=')[1].strip())
        elif 'self.tRCD' in line and '=' in line:
            params['tRCD'] = int(line.split('=')[1].strip())
        elif 'self.tRP' in line and '=' in line:
            params['tRP'] = int(line.split('=')[1].strip())
        elif 'self.tRAS' in line and '=' in line:
            params['tRAS'] = int(line.split('=')[1].strip())
    return params

def plot_score_progression(programs, output_path='evolution_score_progression.png'):
    """Plot score progression over generations."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Group by generation
    generations = {}
    for prog in programs:
        gen = prog['generation']
        if gen not in generations:
            generations[gen] = []
        generations[gen].append(prog['score'])
    
    gen_nums = sorted(generations.keys())
    best_scores = [max(generations[g]) for g in gen_nums]
    avg_scores = [np.mean(generations[g]) for g in gen_nums]
    min_scores = [min(generations[g]) for g in gen_nums]
    
    # Plot 1: Score progression
    ax1.plot(gen_nums, best_scores, 'g-', linewidth=2, marker='o', label='Best Score', markersize=8)
    ax1.plot(gen_nums, avg_scores, 'b--', linewidth=1.5, label='Average Score', alpha=0.7)
    ax1.fill_between(gen_nums, min_scores, best_scores, alpha=0.2, color='blue')
    
    # Highlight key milestones
    global_best = max(best_scores)
    best_gen = gen_nums[best_scores.index(global_best)]
    ax1.axhline(y=global_best, color='red', linestyle=':', alpha=0.5, label=f'Global Best: {global_best:.4f}')
    ax1.axvline(x=best_gen, color='red', linestyle=':', alpha=0.5, label=f'Found at Gen {best_gen}')
    
    ax1.set_xlabel('Generation (Iteration)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax1.set_title('Evolution Score Progression', fontsize=14, fontweight='bold')
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Population diversity (number of programs per generation)
    pop_sizes = [len(generations[g]) for g in gen_nums]
    ax2.bar(gen_nums, pop_sizes, color='steelblue', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Generation (Iteration)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Programs Generated', fontsize=12, fontweight='bold')
    ax2.set_title('Population Size per Generation', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    return fig

def plot_parameter_space(programs, output_path='parameter_space_3d.png'):
    """3D visualization of parameter space exploration."""
    fig = plt.figure(figsize=(16, 12))
    
    # Extract parameters and scores
    data = []
    for prog in programs:
        params = extract_parameters(prog['code'])
        if len(params) == 4:  # Valid extraction
            data.append({
                **params,
                'score': prog['score'],
                'generation': prog['generation']
            })
    
    if not data:
        print("⚠ No valid parameter data found")
        return None
    
    # Create 2x2 subplot grid for different 2D projections
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(2, 2, 3)
    ax4 = fig.add_subplot(2, 2, 4, projection='3d')
    
    # Prepare data
    CLs = [d['CL'] for d in data]
    tRCDs = [d['tRCD'] for d in data]
    tRPs = [d['tRP'] for d in data]
    tRASs = [d['tRAS'] for d in data]
    scores = [d['score'] for d in data]
    gens = [d['generation'] for d in data]
    
    # Normalize scores for color mapping
    norm = plt.Normalize(vmin=min(scores), vmax=max(scores))
    colors = plt.cm.RdYlGn(norm(scores))
    
    # Plot 1: CL vs tRCD
    scatter1 = ax1.scatter(CLs, tRCDs, c=scores, cmap='RdYlGn', s=100, alpha=0.7, edgecolors='black')
    ax1.set_xlabel('CL (cycles)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('tRCD (cycles)', fontsize=11, fontweight='bold')
    ax1.set_title('CL vs tRCD', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    plt.colorbar(scatter1, ax=ax1, label='Score')
    
    # Plot 2: tRP vs tRAS
    scatter2 = ax2.scatter(tRPs, tRASs, c=scores, cmap='RdYlGn', s=100, alpha=0.7, edgecolors='black')
    ax2.set_xlabel('tRP (cycles)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('tRAS (cycles)', fontsize=11, fontweight='bold')
    ax2.set_title('tRP vs tRAS', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    plt.colorbar(scatter2, ax=ax2, label='Score')
    
    # Plot 3: CL vs Score with generation progression
    scatter3 = ax3.scatter(CLs, scores, c=gens, cmap='viridis', s=100, alpha=0.7, edgecolors='black')
    ax3.set_xlabel('CL (cycles)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Score', fontsize=11, fontweight='bold')
    ax3.set_title('CL vs Score (colored by generation)', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    plt.colorbar(scatter3, ax=ax3, label='Generation')
    
    # Plot 4: 3D scatter (CL, tRCD, tRP)
    scatter4 = ax4.scatter(CLs, tRCDs, tRPs, c=scores, cmap='RdYlGn', s=100, alpha=0.7, edgecolors='black')
    ax4.set_xlabel('CL', fontsize=10, fontweight='bold')
    ax4.set_ylabel('tRCD', fontsize=10, fontweight='bold')
    ax4.set_zlabel('tRP', fontsize=10, fontweight='bold')
    ax4.set_title('3D Parameter Space', fontsize=12, fontweight='bold')
    plt.colorbar(scatter4, ax=ax4, label='Score', shrink=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    return fig

def plot_evolution_tree(programs, output_path='evolution_tree.png'):
    """Visualize parent-child relationships in evolution."""
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Build tree structure
    prog_dict = {p['id']: p for p in programs}
    
    # Position nodes by generation (x) and within generation (y)
    gen_positions = {}
    for prog in programs:
        gen = prog['generation']
        if gen not in gen_positions:
            gen_positions[gen] = []
        gen_positions[gen].append(prog['id'])
    
    # Calculate positions
    positions = {}
    for gen, prog_ids in gen_positions.items():
        n_progs = len(prog_ids)
        for i, prog_id in enumerate(sorted(prog_ids)):
            y = (i - n_progs/2) * 2  # Spread vertically
            positions[prog_id] = (gen, y)
    
    # Draw edges (parent -> child)
    for prog in programs:
        if prog['parent_id'] is not None and prog['parent_id'] in positions:
            parent_pos = positions[prog['parent_id']]
            child_pos = positions[prog['id']]
            
            # Color edge by score improvement
            parent_score = prog_dict[prog['parent_id']]['score']
            child_score = prog['score']
            improvement = child_score > parent_score
            
            ax.plot([parent_pos[0], child_pos[0]], 
                   [parent_pos[1], child_pos[1]], 
                   'g-' if improvement else 'gray', 
                   alpha=0.3 if improvement else 0.1,
                   linewidth=2 if improvement else 0.5)
    
    # Draw nodes
    scores = [p['score'] for p in programs]
    norm = plt.Normalize(vmin=min(scores), vmax=max(scores))
    
    for prog in programs:
        if prog['id'] in positions:
            x, y = positions[prog['id']]
            color = plt.cm.RdYlGn(norm(prog['score']))
            ax.scatter(x, y, c=[color], s=200, edgecolors='black', linewidth=1.5, zorder=5)
    
    # Highlight best program
    best_prog = max(programs, key=lambda p: p['score'])
    if best_prog['id'] in positions:
        x, y = positions[best_prog['id']]
        ax.scatter(x, y, s=500, facecolors='none', edgecolors='red', linewidth=3, zorder=6)
        ax.annotate(f'Best: {best_prog["score"]:.4f}', 
                   xy=(x, y), xytext=(x+0.5, y+1),
                   fontsize=10, fontweight='bold', color='red',
                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
    
    ax.set_xlabel('Generation (Iteration)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Population Members', fontsize=12, fontweight='bold')
    ax.set_title('Evolution Tree (Green=Improvement, Gray=No Improvement)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap='RdYlGn', norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label='Score')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    return fig

def plot_feature_space(programs, output_path='feature_space_map.png'):
    """Visualize MAP-Elites feature space."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Extract feature dimensions
    features_data = []
    for prog in programs:
        if prog['features']:
            features_data.append({
                'latency': prog['features'].get('latency_improvement', 0),
                'bandwidth': prog['features'].get('bandwidth_improvement', 0),
                'energy': prog['features'].get('energy_efficiency', 0),
                'score': prog['score'],
                'generation': prog['generation']
            })
    
    if not features_data:
        print("⚠ No feature data found")
        return None
    
    # Prepare data arrays
    lat = [f['latency'] for f in features_data]
    bw = [f['bandwidth'] for f in features_data]
    energy = [f['energy'] for f in features_data]
    scores = [f['score'] for f in features_data]
    gens = [f['generation'] for f in features_data]
    
    # Plot 1: Latency vs Bandwidth
    scatter1 = axes[0, 0].scatter(lat, bw, c=scores, cmap='RdYlGn', s=100, alpha=0.7, edgecolors='black')
    axes[0, 0].set_xlabel('Latency Improvement', fontsize=11, fontweight='bold')
    axes[0, 0].set_ylabel('Bandwidth Improvement', fontsize=11, fontweight='bold')
    axes[0, 0].set_title('Latency vs Bandwidth Trade-off', fontsize=12, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    plt.colorbar(scatter1, ax=axes[0, 0], label='Score')
    
    # Plot 2: Energy vs Score
    scatter2 = axes[0, 1].scatter(energy, scores, c=gens, cmap='viridis', s=100, alpha=0.7, edgecolors='black')
    axes[0, 1].set_xlabel('Energy Efficiency', fontsize=11, fontweight='bold')
    axes[0, 1].set_ylabel('Overall Score', fontsize=11, fontweight='bold')
    axes[0, 1].set_title('Energy Efficiency vs Score', fontsize=12, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)
    plt.colorbar(scatter2, ax=axes[0, 1], label='Generation')
    
    # Plot 3: 3D scatter (latency, bandwidth, energy)
    ax3d = fig.add_subplot(2, 2, 3, projection='3d')
    scatter3 = ax3d.scatter(lat, bw, energy, c=scores, cmap='RdYlGn', s=100, alpha=0.7, edgecolors='black')
    ax3d.set_xlabel('Latency', fontsize=10, fontweight='bold')
    ax3d.set_ylabel('Bandwidth', fontsize=10, fontweight='bold')
    ax3d.set_zlabel('Energy', fontsize=10, fontweight='bold')
    ax3d.set_title('3D Feature Space', fontsize=12, fontweight='bold')
    plt.colorbar(scatter3, ax=ax3d, label='Score', shrink=0.5)
    
    # Plot 4: Feature evolution over generations
    axes[1, 1].plot(gens, lat, 'o-', label='Latency', alpha=0.6)
    axes[1, 1].plot(gens, bw, 's-', label='Bandwidth', alpha=0.6)
    axes[1, 1].plot(gens, energy, '^-', label='Energy', alpha=0.6)
    axes[1, 1].set_xlabel('Generation', fontsize=11, fontweight='bold')
    axes[1, 1].set_ylabel('Feature Value', fontsize=11, fontweight='bold')
    axes[1, 1].set_title('Feature Evolution Over Time', fontsize=12, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    return fig

def generate_summary_report(programs, output_path='evolution_summary.txt'):
    """Generate text summary of evolution results."""
    best_prog = max(programs, key=lambda p: p['score'])
    best_params = extract_parameters(best_prog['code'])
    
    report = []
    report.append("=" * 70)
    report.append("EVOLUTION SUMMARY REPORT")
    report.append("=" * 70)
    report.append("")
    
    # Overall stats
    report.append("Overall Statistics:")
    report.append(f"  Total programs evaluated: {len(programs)}")
    report.append(f"  Generations completed: {max(p['generation'] for p in programs)}")
    report.append(f"  Best score achieved: {best_prog['score']:.6f}")
    report.append(f"  Best found at generation: {best_prog['generation']}")
    report.append("")
    
    # Best configuration
    report.append("Best Configuration:")
    report.append(f"  CL: {best_params.get('CL', 'N/A')}")
    report.append(f"  tRCD: {best_params.get('tRCD', 'N/A')}")
    report.append(f"  tRP: {best_params.get('tRP', 'N/A')}")
    report.append(f"  tRAS: {best_params.get('tRAS', 'N/A')}")
    report.append("")
    
    # Best metrics
    if best_prog['metrics']:
        report.append("Best Program Metrics:")
        for key, value in best_prog['metrics'].items():
            report.append(f"  {key}: {value}")
        report.append("")
    
    # Generation-wise best scores
    gen_best = {}
    for prog in programs:
        gen = prog['generation']
        if gen not in gen_best or prog['score'] > gen_best[gen]:
            gen_best[gen] = prog['score']
    
    report.append("Best Score per Generation:")
    for gen in sorted(gen_best.keys())[:10]:  # First 10 generations
        report.append(f"  Generation {gen:2d}: {gen_best[gen]:.6f}")
    if len(gen_best) > 10:
        report.append(f"  ... ({len(gen_best) - 10} more generations)")
        for gen in sorted(gen_best.keys())[-3:]:  # Last 3 generations
            report.append(f"  Generation {gen:2d}: {gen_best[gen]:.6f}")
    report.append("")
    
    # Parameter space coverage
    all_params = [extract_parameters(p['code']) for p in programs]
    all_params = [p for p in all_params if len(p) == 4]
    
    if all_params:
        report.append("Parameter Space Explored:")
        for param in ['CL', 'tRCD', 'tRP', 'tRAS']:
            values = [p[param] for p in all_params]
            report.append(f"  {param}: min={min(values)}, max={max(values)}, "
                         f"unique={len(set(values))}")
        report.append("")
    
    report.append("=" * 70)
    
    report_text = "\n".join(report)
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(f"✓ Saved: {output_path}")
    print("\n" + report_text)
    return report_text

def main():
    """Generate all visualizations."""
    print("🎨 OpenEvolve Evolution Visualizer")
    print("=" * 70)
    print()
    
    # Check if database exists
    db_path = 'openevolve_output/database/map_elites.db'
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("   Make sure you're running from the openevolve_dram directory")
        return
    
    print(f"📂 Loading data from: {db_path}")
    programs = load_evolution_data(db_path)
    print(f"✓ Loaded {len(programs)} programs")
    print()
    
    # Create output directory
    output_dir = Path('visualizations')
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Saving visualizations to: {output_dir}/")
    print()
    
    # Generate all visualizations
    print("Generating visualizations...")
    print()
    
    plot_score_progression(programs, output_dir / 'evolution_score_progression.png')
    plot_parameter_space(programs, output_dir / 'parameter_space_3d.png')
    plot_evolution_tree(programs, output_dir / 'evolution_tree.png')
    plot_feature_space(programs, output_dir / 'feature_space_map.png')
    generate_summary_report(programs, output_dir / 'evolution_summary.txt')
    
    print()
    print("=" * 70)
    print("✅ All visualizations generated successfully!")
    print()
    print("View results:")
    print(f"  - Score progression: {output_dir}/evolution_score_progression.png")
    print(f"  - Parameter space: {output_dir}/parameter_space_3d.png")
    print(f"  - Evolution tree: {output_dir}/evolution_tree.png")
    print(f"  - Feature space: {output_dir}/feature_space_map.png")
    print(f"  - Summary report: {output_dir}/evolution_summary.txt")
    print()

if __name__ == '__main__':
    main()
