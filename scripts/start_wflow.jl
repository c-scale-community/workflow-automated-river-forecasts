using Wflow
using ArgParse

function parse_commandline()
    s = ArgParseSettings()

    @add_arg_table s begin
        "--toml_filename"
            help = "Location of the wflow TOML file"
            arg_type = String
            default = "wflow_sbm_base.toml"
        "--output_dir" 
            help = "Directory to store model"
            arg_type = String
            default = "output_era/"
        "--instates_filename"
            help = "Location of the states used to initialize the current model run (always point to the ERA5 run!)"
            arg_type = String
            default = "output_era/outstates.nc"
        "--forcing_filename"
            help = "Location of the forcing file"
            arg_type = String
            default = "forcing_ERA5_2021-10-01-2021-10-31.nc"     
    end

    return parse_args(s)
end

function run_wflow()
    parsed_args = parse_commandline()
    toml_filename = parsed_args["toml_filename"]
    output_dir = parsed_args["output_dir"]
    instates_filename = parsed_args["instates_filename"]
    forcing_filename = parsed_args["forcing_filename"]

    # Read TOML file
    config = Wflow.Config(toml_filename)

    # Set correct forcing path 
    config.input.path_forcing = forcing_filename

    # Set model setting to start with states from previous simulation
    config.model.reinit = false
    # Set instates (from the ERA5 simulation)
    config.state.path_input = instates_filename
    # Set location for outstates (only relevant for the ERA5 run)
    config.state.path_output = string(output_dir, "outstates.nc")

    # Set location for csv and nc output
    config.csv.path = string(output_dir, "output.csv")
    config.output.path = string(output_dir, "output.nc")

    # Run wflow model
    Wflow.run(config)
end

run_wflow()