"""
Validation Report Generator

Creates comprehensive validation reports with tables, plots, and summaries.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationReport:
    """
    Generates comprehensive validation reports combining all validation results
    """
    
    def __init__(self, output_dir: str = "models/validation/reports"):
        """
        Initialize ValidationReport
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"ValidationReport initialized, output to: {self.output_dir}")
    
    def generate_summary_report(
        self,
        multi_city_results: Dict[str, Any],
        forecasting_results: Dict[str, Any],
        benchmark_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive summary report
        
        Args:
            multi_city_results: Results from MultiCityValidator
            forecasting_results: Results from ForecastingValidator
            benchmark_results: Results from APIBenchmark
        
        Returns:
            Dictionary with complete report data
        """
        logger.info("\n" + "="*60)
        logger.info("GENERATING COMPREHENSIVE VALIDATION REPORT")
        logger.info("="*60)
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'validation_type': 'Step 6: Multi-City, Forecasting, and API Benchmarking'
            },
            'multi_city_validation': self._summarize_multi_city(multi_city_results),
            'forecasting_validation': self._summarize_forecasting(forecasting_results),
            'api_benchmarking': self._summarize_benchmarking(benchmark_results),
            'overall_rankings': self._generate_rankings(
                multi_city_results,
                forecasting_results
            )
        }
        
        # Save JSON report
        json_path = self.output_dir / f"validation_report_{self.timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"✓ JSON report saved: {json_path}")
        
        # Save markdown report
        md_path = self.output_dir / f"validation_report_{self.timestamp}.md"
        self._save_markdown_report(report, md_path)
        logger.info(f"✓ Markdown report saved: {md_path}")
        
        # Save summary tables
        self._save_summary_tables(report)
        
        return report
    
    def _summarize_multi_city(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize multi-city validation results"""
        summary = {
            'cities_evaluated': [],
            'models_evaluated': list(results.keys()),
            'best_per_city': {},
            'best_overall': None
        }
        
        # Extract unique cities
        cities = set()
        for model_results in results.values():
            cities.update(model_results.keys())
        summary['cities_evaluated'] = sorted(list(cities))
        
        # Find best model per city
        for city in summary['cities_evaluated']:
            best_model = None
            best_r2 = -float('inf')
            
            for model_name, model_results in results.items():
                if city in model_results and 'error' not in model_results[city]:
                    r2 = model_results[city]['r2']
                    if r2 > best_r2:
                        best_r2 = r2
                        best_model = model_name
            
            if best_model:
                summary['best_per_city'][city] = {
                    'model': best_model,
                    'r2': best_r2,
                    'rmse': results[best_model][city]['rmse'],
                    'mae': results[best_model][city]['mae']
                }
        
        # Find best overall model (average R² across cities)
        best_model = None
        best_avg_r2 = -float('inf')
        
        for model_name, model_results in results.items():
            r2_scores = [m['r2'] for c, m in model_results.items() if 'error' not in m]
            if r2_scores:
                avg_r2 = np.mean(r2_scores)
                if avg_r2 > best_avg_r2:
                    best_avg_r2 = avg_r2
                    best_model = model_name
        
        summary['best_overall'] = {
            'model': best_model,
            'avg_r2': best_avg_r2
        }
        
        return summary
    
    def _summarize_forecasting(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize forecasting validation results"""
        summary = {
            'horizons_evaluated': [],
            'models_evaluated': list(results.keys()),
            'best_per_horizon': {},
            'degradation_analysis': {}
        }
        
        # Extract unique horizons
        horizons = set()
        for model_results in results.values():
            horizons.update(model_results.keys())
        summary['horizons_evaluated'] = sorted(list(horizons))
        
        # Find best model per horizon
        for horizon in summary['horizons_evaluated']:
            best_model = None
            best_rmse = float('inf')
            
            for model_name, model_results in results.items():
                if horizon in model_results and 'error' not in model_results[horizon]:
                    rmse = model_results[horizon]['rmse']
                    if rmse < best_rmse:
                        best_rmse = rmse
                        best_model = model_name
            
            if best_model:
                summary['best_per_horizon'][horizon] = {
                    'model': best_model,
                    'rmse': best_rmse,
                    'r2': results[best_model][horizon]['r2']
                }
        
        # Analyze performance degradation with horizon
        for model_name, model_results in results.items():
            horizons_sorted = sorted([h for h in model_results.keys() if 'error' not in model_results[h]])
            if len(horizons_sorted) >= 2:
                first_rmse = model_results[horizons_sorted[0]]['rmse']
                last_rmse = model_results[horizons_sorted[-1]]['rmse']
                degradation = ((last_rmse - first_rmse) / first_rmse) * 100
                
                summary['degradation_analysis'][model_name] = {
                    'rmse_increase_%': degradation,
                    'from_horizon': horizons_sorted[0],
                    'to_horizon': horizons_sorted[-1]
                }
        
        return summary
    
    def _summarize_benchmarking(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize API benchmarking results"""
        if not results or 'error' in results:
            return {'status': 'No benchmarking data available'}
        
        summary = {
            'research_comparisons': results.get('research_comparisons', {}),
            'api_comparisons': results.get('api_comparisons', {}),
            'overall_performance': results.get('overall_performance', {})
        }
        
        return summary
    
    def _generate_rankings(
        self,
        multi_city_results: Dict[str, Any],
        forecasting_results: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate overall model rankings"""
        
        # Calculate scores for each model
        scores = {}
        
        for model_name in multi_city_results.keys():
            # Multi-city average R²
            city_r2_scores = [
                m['r2'] for m in multi_city_results[model_name].values()
                if 'error' not in m
            ]
            avg_city_r2 = np.mean(city_r2_scores) if city_r2_scores else 0
            
            # Forecasting average RMSE
            forecast_rmse_scores = [
                m['rmse'] for m in forecasting_results.get(model_name, {}).values()
                if 'error' not in m
            ]
            avg_forecast_rmse = np.mean(forecast_rmse_scores) if forecast_rmse_scores else float('inf')
            
            # Combined score (higher is better)
            # Normalize RMSE to 0-1 scale (lower is better)
            rmse_score = 1 / (1 + avg_forecast_rmse / 100) if avg_forecast_rmse < float('inf') else 0
            
            combined_score = (avg_city_r2 * 0.6) + (rmse_score * 0.4)
            
            scores[model_name] = {
                'model': model_name,
                'combined_score': combined_score,
                'avg_r2': avg_city_r2,
                'avg_rmse': avg_forecast_rmse
            }
        
        # Sort by combined score
        ranked = sorted(scores.values(), key=lambda x: x['combined_score'], reverse=True)
        
        return {
            'overall_ranking': ranked,
            'ranking_methodology': 'Combined score: 60% multi-city R² + 40% forecasting RMSE'
        }
    
    def _save_markdown_report(self, report: Dict[str, Any], filepath: Path):
        """Save report as markdown"""
        
        with open(filepath, 'w') as f:
            f.write("# AQI Prediction Model Validation Report\n\n")
            f.write(f"**Generated:** {report['metadata']['generated_at']}\n\n")
            f.write(f"**Validation Type:** {report['metadata']['validation_type']}\n\n")
            
            f.write("---\n\n")
            
            # Multi-City Validation
            f.write("## 1. Multi-City Validation\n\n")
            mc = report['multi_city_validation']
            f.write(f"**Cities Evaluated:** {', '.join(mc['cities_evaluated'])}\n\n")
            f.write(f"**Models Evaluated:** {', '.join(mc['models_evaluated'])}\n\n")
            
            f.write("### Best Model Per City\n\n")
            f.write("| City | Best Model | R² Score | RMSE | MAE |\n")
            f.write("|------|------------|----------|------|-----|\n")
            for city, data in mc['best_per_city'].items():
                f.write(f"| {city} | {data['model']} | {data['r2']:.4f} | "
                       f"{data['rmse']:.2f} | {data['mae']:.2f} |\n")
            
            f.write(f"\n**Best Overall Model:** {mc['best_overall']['model']} "
                   f"(Avg R² = {mc['best_overall']['avg_r2']:.4f})\n\n")
            
            # Forecasting Validation
            f.write("## 2. Forecasting Validation (1-48h)\n\n")
            fc = report['forecasting_validation']
            f.write(f"**Horizons Evaluated:** {', '.join(map(str, fc['horizons_evaluated']))} hours\n\n")
            
            f.write("### Best Model Per Horizon\n\n")
            f.write("| Horizon (h) | Best Model | RMSE | R² Score |\n")
            f.write("|-------------|------------|------|----------|\n")
            for horizon, data in fc['best_per_horizon'].items():
                f.write(f"| {horizon} | {data['model']} | {data['rmse']:.2f} | {data['r2']:.4f} |\n")
            
            f.write("\n### Performance Degradation Analysis\n\n")
            f.write("| Model | RMSE Increase (%) | Horizon Range |\n")
            f.write("|-------|-------------------|---------------|\n")
            for model, data in fc['degradation_analysis'].items():
                f.write(f"| {model} | {data['rmse_increase_%']:+.1f}% | "
                       f"{data['from_horizon']}h → {data['to_horizon']}h |\n")
            
            # Overall Rankings
            f.write("\n## 3. Overall Model Rankings\n\n")
            rankings = report['overall_rankings']
            f.write(f"**Methodology:** {rankings['ranking_methodology']}\n\n")
            
            f.write("| Rank | Model | Combined Score | Avg R² | Avg RMSE |\n")
            f.write("|------|-------|----------------|--------|----------|\n")
            for i, model_data in enumerate(rankings['overall_ranking'], 1):
                f.write(f"| {i} | {model_data['model']} | {model_data['combined_score']:.4f} | "
                       f"{model_data['avg_r2']:.4f} | {model_data['avg_rmse']:.2f} |\n")
            
            f.write("\n---\n\n")
            f.write("## Recommendations\n\n")
            
            best_model = rankings['overall_ranking'][0]['model']
            f.write(f"1. **Recommended Model for Production:** {best_model}\n")
            f.write(f"2. **Multi-City Deployment:** Consider city-specific fine-tuning\n")
            f.write(f"3. **Forecast Horizon:** Best performance up to 24h, degradation beyond\n")
            f.write(f"4. **Continuous Monitoring:** Compare against commercial APIs regularly\n")
    
    def _save_summary_tables(self, report: Dict[str, Any]):
        """Save summary tables as CSV files"""
        
        # Multi-city summary
        mc_data = []
        for city, data in report['multi_city_validation']['best_per_city'].items():
            mc_data.append({
                'City': city,
                'Best Model': data['model'],
                'R² Score': data['r2'],
                'RMSE': data['rmse'],
                'MAE': data['mae']
            })
        
        if mc_data:
            df_mc = pd.DataFrame(mc_data)
            mc_path = self.output_dir / f"multi_city_summary_{self.timestamp}.csv"
            df_mc.to_csv(mc_path, index=False)
            logger.info(f"✓ Multi-city summary saved: {mc_path}")
        
        # Forecasting summary
        fc_data = []
        for horizon, data in report['forecasting_validation']['best_per_horizon'].items():
            fc_data.append({
                'Horizon (hours)': horizon,
                'Best Model': data['model'],
                'RMSE': data['rmse'],
                'R² Score': data['r2']
            })
        
        if fc_data:
            df_fc = pd.DataFrame(fc_data)
            fc_path = self.output_dir / f"forecasting_summary_{self.timestamp}.csv"
            df_fc.to_csv(fc_path, index=False)
            logger.info(f"✓ Forecasting summary saved: {fc_path}")
        
        # Rankings
        rankings = report['overall_rankings']['overall_ranking']
        if rankings:
            df_rank = pd.DataFrame(rankings)
            rank_path = self.output_dir / f"model_rankings_{self.timestamp}.csv"
            df_rank.to_csv(rank_path, index=False)
            logger.info(f"✓ Model rankings saved: {rank_path}")
    
    def plot_validation_results(
        self,
        multi_city_results: Dict[str, Any],
        forecasting_results: Dict[str, Any]
    ):
        """
        Generate comprehensive validation plots
        
        Args:
            multi_city_results: Multi-city validation results
            forecasting_results: Forecasting validation results
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            sns.set_style("whitegrid")
            
            fig = plt.figure(figsize=(16, 12))
            gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
            
            # 1. Multi-city R² comparison
            ax1 = fig.add_subplot(gs[0, 0])
            self._plot_multi_city_comparison(multi_city_results, ax1, metric='r2')
            
            # 2. Multi-city RMSE comparison
            ax2 = fig.add_subplot(gs[0, 1])
            self._plot_multi_city_comparison(multi_city_results, ax2, metric='rmse')
            
            # 3. Forecasting horizon performance
            ax3 = fig.add_subplot(gs[1, :])
            self._plot_forecast_horizons(forecasting_results, ax3)
            
            # 4. Model rankings
            ax4 = fig.add_subplot(gs[2, 0])
            self._plot_model_rankings(multi_city_results, forecasting_results, ax4)
            
            # 5. Performance heatmap
            ax5 = fig.add_subplot(gs[2, 1])
            self._plot_performance_heatmap(multi_city_results, ax5)
            
            plt.suptitle('AQI Prediction Model Validation Results', fontsize=16, y=0.995)
            
            plot_path = self.output_dir / f"validation_plots_{self.timestamp}.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            logger.info(f"✓ Validation plots saved: {plot_path}")
            plt.close()
            
        except ImportError:
            logger.warning("Matplotlib/Seaborn not available for plotting")
    
    def _plot_multi_city_comparison(self, results: Dict[str, Any], ax, metric='r2'):
        """Plot multi-city comparison bar chart"""
        import matplotlib.pyplot as plt
        
        cities = []
        models = list(results.keys())
        
        # Collect all cities
        for model_results in results.values():
            cities.extend(model_results.keys())
        cities = sorted(list(set(cities)))
        
        # Prepare data
        data = {model: [] for model in models}
        
        for city in cities:
            for model in models:
                if city in results[model] and 'error' not in results[model][city]:
                    data[model].append(results[model][city][metric])
                else:
                    data[model].append(np.nan)
        
        # Plot
        x = np.arange(len(cities))
        width = 0.8 / len(models)
        
        for i, model in enumerate(models):
            offset = (i - len(models)/2) * width + width/2
            ax.bar(x + offset, data[model], width, label=model, alpha=0.8)
        
        ax.set_xlabel('City', fontweight='bold')
        ax.set_ylabel(metric.upper() if metric != 'r2' else 'R² Score', fontweight='bold')
        ax.set_title(f'Multi-City {metric.upper()} Comparison', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(cities, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_forecast_horizons(self, results: Dict[str, Any], ax):
        """Plot forecast performance across horizons"""
        for model_name, model_results in results.items():
            horizons = []
            rmse_vals = []
            
            for horizon in sorted(model_results.keys()):
                if 'error' not in model_results[horizon]:
                    horizons.append(horizon)
                    rmse_vals.append(model_results[horizon]['rmse'])
            
            if horizons:
                ax.plot(horizons, rmse_vals, marker='o', label=model_name, linewidth=2)
        
        ax.set_xlabel('Forecast Horizon (hours)', fontweight='bold')
        ax.set_ylabel('RMSE', fontweight='bold')
        ax.set_title('Forecast Performance Across Horizons', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_model_rankings(self, multi_city_results, forecasting_results, ax):
        """Plot overall model rankings"""
        # Calculate combined scores
        scores = {}
        for model_name in multi_city_results.keys():
            city_r2 = [m['r2'] for m in multi_city_results[model_name].values() if 'error' not in m]
            scores[model_name] = np.mean(city_r2) if city_r2 else 0
        
        models = list(scores.keys())
        values = list(scores.values())
        
        ax.barh(models, values, alpha=0.7)
        ax.set_xlabel('Average R² Score', fontweight='bold')
        ax.set_title('Model Rankings (Multi-City Average)', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
    
    def _plot_performance_heatmap(self, results: Dict[str, Any], ax):
        """Plot performance heatmap"""
        import seaborn as sns
        
        # Prepare data matrix
        cities = []
        models = list(results.keys())
        
        for model_results in results.values():
            cities.extend(model_results.keys())
        cities = sorted(list(set(cities)))
        
        data_matrix = []
        for model in models:
            row = []
            for city in cities:
                if city in results[model] and 'error' not in results[model][city]:
                    row.append(results[model][city]['r2'])
                else:
                    row.append(np.nan)
            data_matrix.append(row)
        
        # Plot heatmap
        sns.heatmap(
            data_matrix,
            xticklabels=cities,
            yticklabels=models,
            annot=True,
            fmt='.3f',
            cmap='RdYlGn',
            vmin=0,
            vmax=1,
            ax=ax,
            cbar_kws={'label': 'R² Score'}
        )
        ax.set_title('Performance Heatmap (R² Score)', fontweight='bold')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')


if __name__ == "__main__":
    print("Testing ValidationReport...")
    print("=" * 60)
    
    # Create dummy results
    multi_city_results = {
        'LinearRegression': {
            'Delhi': {'r2': 0.72, 'rmse': 42.5, 'mae': 30.2},
            'Mumbai': {'r2': 0.75, 'rmse': 38.1, 'mae': 27.5}
        },
        'XGBoost': {
            'Delhi': {'r2': 0.78, 'rmse': 38.2, 'mae': 27.1},
            'Mumbai': {'r2': 0.80, 'rmse': 35.5, 'mae': 25.2}
        }
    }
    
    forecasting_results = {
        'LinearRegression': {
            1: {'r2': 0.80, 'rmse': 35.0, 'n_samples': 100},
            6: {'r2': 0.75, 'rmse': 40.0, 'n_samples': 100}
        },
        'XGBoost': {
            1: {'r2': 0.85, 'rmse': 30.0, 'n_samples': 100},
            6: {'r2': 0.82, 'rmse': 33.0, 'n_samples': 100}
        }
    }
    
    benchmark_results = {}
    
    # Generate report
    reporter = ValidationReport()
    report = reporter.generate_summary_report(
        multi_city_results,
        forecasting_results,
        benchmark_results
    )
    
    print("\n✓ Report generated successfully")
    print(f"  Best overall model: {report['overall_rankings']['overall_ranking'][0]['model']}")
    
    print("\n✅ ValidationReport test complete!")
