FROM quay.io/jupyter/scipy-notebook:2024-09-02

# Install required Python libraries
RUN pip install \
    duckdb \
    redis==5.0.0 \
    neo4j \
    psycopg2-binary \
    boto3 \
    redisearch[vector] \
    pymongo \
    transformers accelerate torch safetensors  # Add Hugging Face dependencies

# Configure Jupyter to disable token/password
RUN jupyter notebook --generate-config && \
    echo "c.NotebookApp.token = ''" >> /home/jovyan/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.password = ''" >> /home/jovyan/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.allow_origin = '*'" >> /home/jovyan/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.ip = '0.0.0.0'" >> /home/jovyan/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.open_browser = False" >> /home/jovyan/.jupyter/jupyter_notebook_config.py

# Fix permissions for the installed libraries
USER root
RUN fix-permissions /home/$NB_USER
USER $NB_USER