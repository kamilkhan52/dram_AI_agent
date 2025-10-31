#!/usr/bin/env python3
"""
Visualize OpenEvolve evolution from log files (for version 0.2.18).
Since the database doesn't exist in this version, parse logs instead.
"""

import re
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import seaborn as sns
from collections import defaultdict

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def parse_evolution_log(log_file):
    """Parse the OpenEvolve log file to extract evolution data."""
    programs = []
    best_discoveries = []
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        # Match iteration completion lines
        # Format: "Iteration X: Program UUID ... completed in Ys"
        # Next line: "Metrics: combined_score=1.0825, ..."
        iter_match = re.search(r'Iteration (\d+):.*completed in ([\d.]+)s', line)
        if iter_match:
            iteration = int(iter_match.group(1))
            time_taken = float(iter_match.group(2))
            
            # Look for combined_score in the next line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                score_match = re.search(r'combined_score=([\d.]+)', next_line)
                if score_match:
                    score = float(score_match.group(1))
                    programs.append({
                        'iteration': iteration,
                        'score': score,
                        'time': time_taken
                    })
        
        # Match "New best solution found" lines
        best_match = re.search(r'New best solution found at iteration (\d+)', line)
        if best_match:
            iteration = int(best_match.group(1))
            # Look for the score in previous lines (already captured in programs list)
            matching_programs = [p for p in programs if p['iteration'] == iteration]
            if matching_programs:
                best_discoveries.append({
                    'iteration': iteration,
                    'score': matching_programs[-1]['score'],
                    'is_best': True
                })
    
    # Merge best discoveries into programs list
    for best in best_discoveries:
        for prog in programs:
            if prog['iteration'] == best['iteration'] and prog['score'] == best['score']:
                prog['is_best'] = True
                break
    
    return programs

def load_best_program_info():
    """Load the best program info JSON."""
    json_path = Path('openevolve_output/best/best_program_info.json')
    if json_path.exists():
        with open(json_path, 'r') as f:
            return json.load(f)
    return None

def extract_parameters_from_file(filepath='openevolve_output/best/best_program.py'):
    """Extract parameters from the best program file."""
    params = {}
    try:
        with open(filepath, 'r') as f:
            code = f.read()
            for line in code.split('\n'):
                if 'self.CL' in line and '=' in line and '#' not in line.split('=')[0]:
                    value_str = line.split('=')[1].split('#')[0].strip()
                    params['CL'] = int(value_str)
                elif 'self.tRCD' in line and '=' in line and '#' not in line.split('=')[0]:
                    value_str = line.split('=')[1].split('#')[0].strip()
                    params['tRCD'] = int(value_str)
                elif 'self.tRP' in line and '=' in line and '#' not in line.split('=')[0]:
                    value_str = line.split('=')[1].split('#')[0].strip()
                    params['tRP'] = int(value_str)
                elif 'self.tRAS' in line and '=' in line and '#' not in line.split('=')[0]:
                    value_str = line.split('=')[1].split('#')[0].strip()
                    params['tRAS'] = int(value_str)
    except Exception as e:
        print(f"Warning: Could not extract parameters: {e}")
    return params

def plot_score_progression_from_logs(log_file, output_path='evolution_score_progression.png'):
    """Plot score progression from log file."""
    programs = parse_evolution_log(log_file)
    
    if not programs:
        print("⚠ No program data found in logs")
        return None
    
    # Group by iteration
    iterations = defaultdict(list)
    best_scores = {}
    
    for prog in programs:
        iterations[prog['iteration']].append(prog['score'])
        if prog.get('is_best'):
            best_scores[prog['iteration']] = prog['score']
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Calculate statistics per iteration
    iter_nums = sorted(iterations.keys())
    max_scores = [max(iterations[i]) for i in iter_nums]
    avg_scores = [np.mean(iterations[i]) for i in iter_nums]
    min_scores = [min(iterations[i]) for i in iter_nums]
    
    # Plot 1: Score progression
    ax1.plot(iter_nums, max_scores, 'g-', linewidth=2, marker='o', label='Best Score', markersize=8)
    ax1.plot(iter_nums, avg_scores, 'b--', linewidth=1.5, label='Average Score', alpha=0.7)
    ax1.fill_between(iter_nums, min_scores, max_scores, alpha=0.2, color='blue')
    
    # Mark new best discoveries
    if best_scores:
        best_iters = sorted(best_scores.keys())
        best_vals = [best_scores[i] for i in best_iters]
        ax1.scatter(best_iters, best_vals, color='red', s=200, marker='*', 
                   label='New Best Found', zorder=10, edgecolors='darkred', linewidth=2)
        
        # Annotate best scores
        for i, (iter_num, score) in enumerate(best_scores.items()):
            ax1.annotate(f'{score:.4f}', 
                        xy=(iter_num, score), 
                        xytext=(5, 5 if i % 2 == 0 else -15),
                        textcoords='offset points',
                        fontsize=9, fontweight='bold', color='red',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    # Global best line
    global_best = max(max_scores)
    ax1.axhline(y=global_best, color='red', linestyle=':', alpha=0.5, 
               label=f'Global Best: {global_best:.4f}')
    
    ax1.set_xlabel('Iteration', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax1.set_title('Evolution Score Progression', fontsize=14, fontweight='bold')
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Evaluations per iteration
    eval_counts = [len(iterations[i]) for i in iter_nums]
    ax2.bar(iter_nums, eval_counts, color='steelblue', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Iteration', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Number of Evaluations', fontsize=12, fontweight='bold')
    ax2.set_title('Evaluations per Iteration', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    return fig

def plot_improvement_timeline(log_file, output_path='improvement_timeline.png'):
    """Plot when improvements were discovered."""
    programs = parse_evolution_log(log_file)
    best_programs = [p for p in programs if p.get('is_best')]
    
    if not best_programs:
        print("⚠ No best program milestones found")
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Extract data
    iterations = [p['iteration'] for p in best_programs]
    scores = [p['score'] for p in best_programs]
    
    # Plot as step function
    ax.step(iterations, scores, where='post', linewidth=3, color='green', alpha=0.7)
    ax.scatter(iterations, scores, s=300, color='red', marker='*', 
              edgecolors='darkred', linewidth=2, zorder=10, label='New Best Found')
    
    # Annotate each milestone
    for i, (iter_num, score) in enumerate(zip(iterations, scores)):
        improvement = ((score - scores[0]) / scores[0] * 100) if i > 0 else 0
        ax.annotate(f'Iter {iter_num}\n{score:.4f}\n(+{improvement:.1f}%)', 
                   xy=(iter_num, score),
                   xytext=(0, 20 if i % 2 == 0 else -40),
                   textcoords='offset points',
                   ha='center',
                   fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    ax.set_xlabel('Iteration', fontsize=12, fontweight='bold')
    ax.set_ylabel('Best Score', fontsize=12, fontweight='bold')
    ax.set_title('Timeline of Best Solution Discoveries', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    return fig

def generate_summary_report(log_file, output_path='evolution_summary.txt'):
    """Generate text summary from logs and best program."""
    programs = parse_evolution_log(log_file)
    best_programs = [p for p in programs if p.get('is_best')]
    best_info = load_best_program_info()
    best_params = extract_parameters_from_file()
    
    report = []
    report.append("=" * 70)
    report.append("EVOLUTION SUMMARY REPORT")
    report.append("=" * 70)
    report.append("")
    
    # Overall stats
    iterations = defaultdict(list)
    for prog in programs:
        iterations[prog['iteration']].append(prog['score'])
    
    report.append("Overall Statistics:")
    report.append(f"  Total iterations completed: {max(iterations.keys()) if iterations else 0}")
    report.append(f"  Total evaluations: {len(programs)}")
    if iterations:
        report.append(f"  Average evaluations per iteration: {len(programs) / len(iterations):.1f}")
    else:
        report.append(f"  Average evaluations per iteration: N/A")
    
    if best_programs:
        report.append(f"  Best score achieved: {best_programs[-1]['score']:.6f}")
        report.append(f"  Best found at iteration: {best_programs[-1]['iteration']}")
        report.append(f"  Number of improvements: {len(best_programs)}")
    report.append("")
    
    # Best configuration
    if best_params:
        report.append("Best Configuration (from best_program.py):")
        report.append(f"  CL: {best_params.get('CL', 'N/A')} cycles")
        report.append(f"  tRCD: {best_params.get('tRCD', 'N/A')} cycles")
        report.append(f"  tRP: {best_params.get('tRP', 'N/A')} cycles")
        report.append(f"  tRAS: {best_params.get('tRAS', 'N/A')} cycles")
        report.append("")
    
    # Best program info
    if best_info:
        report.append("Best Program Metrics (from best_program_info.json):")
        for key, value in best_info.items():
            if key != 'code':  # Skip code field
                report.append(f"  {key}: {value}")
        report.append("")
    
    # Improvement timeline
    if best_programs:
        report.append("Improvement Timeline:")
        for i, prog in enumerate(best_programs):
            improvement_pct = 0
            if i > 0:
                improvement_pct = ((prog['score'] - best_programs[0]['score']) / 
                                  best_programs[0]['score'] * 100)
            report.append(f"  Iteration {prog['iteration']:2d}: "
                         f"score = {prog['score']:.6f} "
                         f"(+{improvement_pct:.2f}%)")
        report.append("")
    
    # Score statistics
    if iterations:
        all_scores = [score for scores in iterations.values() for score in scores]
        report.append("Score Distribution:")
        report.append(f"  Minimum: {min(all_scores):.6f}")
        report.append(f"  Maximum: {max(all_scores):.6f}")
        report.append(f"  Mean: {np.mean(all_scores):.6f}")
        report.append(f"  Median: {np.median(all_scores):.6f}")
        report.append(f"  Std Dev: {np.std(all_scores):.6f}")
        report.append("")
    
    report.append("=" * 70)
    
    report_text = "\n".join(report)
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(f"✓ Saved: {output_path}")
    print("\n" + report_text)
    return report_text

def main():
    """Generate visualizations from log files."""
    print("🎨 OpenEvolve Evolution Visualizer (Log-based)")
    print("=" * 70)
    print()
    
    # Find log file
    log_dir = Path('openevolve_output/logs')
    if not log_dir.exists():
        print(f"❌ Log directory not found: {log_dir}")
        return
    
    log_files = sorted(log_dir.glob('openevolve_*.log'))
    if not log_files:
        print(f"❌ No log files found in: {log_dir}")
        return
    
    # Use the most recent log file
    log_file = log_files[-1]
    print(f"📂 Reading log file: {log_file.name}")
    print()
    
    # Create output directory
    output_dir = Path('visualizations')
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Saving visualizations to: {output_dir}/")
    print()
    
    # Generate visualizations
    print("Generating visualizations...")
    print()
    
    plot_score_progression_from_logs(log_file, output_dir / 'evolution_score_progression.png')
    plot_improvement_timeline(log_file, output_dir / 'improvement_timeline.png')
    generate_summary_report(log_file, output_dir / 'evolution_summary.txt')
    
    print()
    print("=" * 70)
    print("✅ All visualizations generated successfully!")
    print()
    print("View results:")
    print(f"  - Score progression: {output_dir}/evolution_score_progression.png")
    print(f"  - Improvement timeline: {output_dir}/improvement_timeline.png")
    print(f"  - Summary report: {output_dir}/evolution_summary.txt")
    print()
    print("Note: OpenEvolve 0.2.18 doesn't provide detailed genealogy data,")
    print("      so some visualizations (evolution tree, parameter space)")
    print("      cannot be generated without parsing all intermediate programs.")
    print()

if __name__ == '__main__':
    main()
