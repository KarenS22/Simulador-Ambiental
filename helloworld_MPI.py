#hello.py
from mpi4py import MPI
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

print(f"[START] rank={rank} size={size}", flush=True)

time.sleep(50)

print(f"[MID] rank={rank}", flush=True)

comm.Barrier()

print(f"[END] rank={rank}", flush=True)
