import yaml
import sys
import os
import argparse
from pathlib import Path
import subprocess
import re

def rep(x):
    return f'"{x}"' if type(x) is str and '"' not in x else x

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--julia-sim-path", type = Path, default="../BiomassSuccession")
    parser.add_argument("--data-path", type = Path, default="./data")
    parser.add_argument("--output-path", type = Path, default="./outputs")
    parser.add_argument("--scenario", type = Path)
    args = parser.parse_args()

    assert args.julia_sim_path.exists()
    assert args.scenario.exists()

    with open(args.scenario,'r') as f:
        scenario= yaml.safe_load(f)

    print(scenario)

    def make_absolute_path(scenario, scenario_parent, path_key, default):
        path = Path(scenario.pop(path_key,default))
        path = path if path.is_absolute() else (scenario_parent / path).resolve()
        scenario[path_key]  = str(path)




    scenario=scenario['scenario']
    scenario_name = scenario.pop('name', args.scenario.parent.stem)
    make_absolute_path(scenario, args.scenario.parent, 'data_dir', './data')
    make_absolute_path(scenario, args.scenario.parent, 'output_dir', './outputs' )
    scenario['output_dir'] = str(Path(scenario['output_dir']) / scenario_name)
    output_args  = [('output_dir',scenario['output_dir'])]

    threads = scenario.pop("threads", "auto")
    julia_cmd = [args.julia_sim_path / "julia_gdal.sh", f"--project={args.julia_sim_path}", f"--threads={threads}"]
    biomass_tmp_str = '''using BiomassSuccession;BiomassSuccession.'''

    sim_args_str = ', '.join(f"{k}={rep(v)}" for k,v in scenario.items())
    sim_func_str =f'''simulate_treemap_raster(;{sim_args_str})''' 
    sim_cmd = julia_cmd + ["-e",biomass_tmp_str + sim_func_str]

    raster_args_str = ', '.join(f"{k}={rep(v)}" for k,v in [('data_dir',scenario['data_dir']),('ref_raster_path',scenario['treemap_raster'])]+output_args)
    raster_func_str =f'''generate_rasters_from_output(;{raster_args_str})''' 
    raster_cmd = julia_cmd + ["-e",biomass_tmp_str + raster_func_str]
    #julia_cmd_str =f"julia --project={args.julia_sim_path} --threads={threads}"
    #sim_args_str = ', '.join(f"{k}={rep(v)}" for k,v in list(scenario.items())+output_args)
    #raster_args_str = ', '.join(f"{k}={rep(v)}" for k,v in [('ref_raster_path',scenario['treemap_raster_path'])]+output_args)
    #cmd_str = f"{julia_cmd_str} -e 'using BiomassSuccession;BiomassSuccession.simulate_raster(;{sim_args_str})'"
    #coalesce_str = f"""{julia_cmd_str} -e 'using BiomassSuccession;BiomassSuccession.generate_rasters_from_output(;{raster_args_str})'"""
    print(sim_cmd)
    input("sim?")
    res = subprocess.call(sim_cmd)
    print(res)
    print(raster_cmd)
    input("rasters?")
    res = subprocess.call(raster_cmd)
    print(res)
    if not res:
        sys.exit(1)
    
    input("db?")
    res = os.system("./parquet_sqlite.sh")
    print(res)
    if not res:
        sys.exit(1)
