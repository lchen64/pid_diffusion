from setuptools import setup

setup(
    name="consistency-models",
    py_modules=["cm", "evaluations"],
    install_requires=[
        "psutil",
        "blobfile==3.0.0",
        "clean-fid",
        "tqdm",
        "numpy==1.23.0",
        "scipy",
        "markdown>=2.6.8",
        "protobuf>=3.19.6",
        "pandas",
        "Cython",
        "piq==0.7.0",
        "joblib==0.14.0",
        "albumentations==0.4.3",
        "lmdb",
        "clip @ git+https://github.com/openai/CLIP.git",
        "torch==2.0.1",
        "torchvision",
        "flash-attn==0.2.8",
        "pillow",
    ],
)
