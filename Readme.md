# this project makes heavy use of bmdcluster by Carson Sprock
# https://github.com/csprock/bmdcluster.git

# create a new environment for the project
conda-env create -n new_env_name -f=testEnv2.yml

# activate this new environment
conda activate name_of_env

# install docx from pip
# to do this ensure you are in anaconda prompt and the virtual env is activated
pip install python-docx
pip install beautifulsoup4
pip install bmdcluster

# image generation requires psutil package
conda install --name ScrapePnetEnv -c plotly plotly-orca psutil requests