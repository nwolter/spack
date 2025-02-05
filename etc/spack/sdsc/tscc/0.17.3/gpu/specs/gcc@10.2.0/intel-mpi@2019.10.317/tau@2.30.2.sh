#!/usr/bin/env bash

#SBATCH --job-name=tau@2.30.2
#SBATCH --account=sys200
#SBATCH --partition=hotel-gpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH -w gpu1
#SBATCH --time=00:30:00
#SBATCH --output=%x.o%j.%N

declare -xr LOCAL_TIME="$(date +'%Y%m%dT%H%M%S%z')"
declare -xir UNIX_TIME="$(date +'%s')"

declare -xr SYSTEM_NAME='tscc'

declare -xr SPACK_VERSION='0.17.3'
declare -xr SPACK_INSTANCE_NAME='gpu'
declare -xr SPACK_INSTANCE_DIR="/cm/shared/apps/spack/${SPACK_VERSION}/${SPACK_INSTANCE_NAME}"

declare -xr SLURM_JOB_SCRIPT="$(scontrol show job ${SLURM_JOB_ID} | awk -F= '/Command=/{print $2}')"
declare -xr SLURM_JOB_MD5SUM="$(md5sum ${SLURM_JOB_SCRIPT})"

declare -xr SCHEDULER_MODULE='slurm'

echo "${UNIX_TIME} ${SLURM_JOB_ID} ${SLURM_JOB_MD5SUM} ${SLURM_JOB_DEPENDENCY}" 
echo ""

cat "${SLURM_JOB_SCRIPT}"

module purge
module load "${SCHEDULER_MODULE}"
module list
. "${SPACK_INSTANCE_DIR}/share/spack/setup-env.sh"

# >> 16    Error: Cannot access MPI include directory /home/mkandes/cm/shared/a
#           pps/spack/0.17.3/gpu/opt/spack/linux-rocky8-cascadelake/gcc-10.2.0/i
#           ntel-mpi-2019.10.317-jhyxn2gkqptkwz23tocb2darb4lfirxb/include

declare -xr SPACK_PACKAGE='tau@2.30.2'
declare -xr SPACK_COMPILER='gcc@10.2.0'
declare -xr SPACK_VARIANTS='~adios2 +binutils ~comm ~craycnl +cuda +elf +fortran ~gasnet +io ~level_zero +libdwarf +libunwind ~likwid +mpi ~ompt ~opari ~opencl ~openmp +otf2 +papi +pdt ~phase ~ppc64le ~profileparam +pthreads +python ~rocm ~rocprofiler ~roctracer ~scorep ~shmem +sqlite ~x86_64'
declare -xr SPACK_DEPENDENCIES="^intel-mpi@2019.10.317/$(spack find --format '{hash:7}' intel-mpi@2019.10.317 % ${SPACK_COMPILER}) ^papi@6.0.0.1/$(spack find --format '{hash:7}' papi@6.0.0.1 % ${SPACK_COMPILER}) ^python@3.8.12/$(spack find --format '{hash:7}' python@3.8.12 % ${SPACK_COMPILER}) ^boost@1.77.0/$(spack find --format '{hash:7}' boost@1.77.0 % ${SPACK_COMPILER} ~mpi)"
declare -xr SPACK_SPEC="${SPACK_PACKAGE} % ${SPACK_COMPILER} ${SPACK_VARIANTS} ${SPACK_DEPENDENCIES}"

printenv

spack config get compilers
spack config get config  
spack config get mirrors
spack config get modules
spack config get packages
spack config get repos
spack config get upstreams

spack spec --long --namespaces --types "${SPACK_SPEC}"
if [[ "${?}" -ne 0 ]]; then
  echo 'ERROR: spack concretization failed.'
  exit 1
fi

time -p spack install -v --keep-prefix --jobs "${SLURM_CPUS_PER_TASK}" --fail-fast --yes-to-all "${SPACK_SPEC}"
if [[ "${?}" -ne 0 ]]; then
  echo 'ERROR: spack install failed.'
  exit 1
fi

spack module lmod refresh --delete-tree -y

sbatch --dependency="afterok:${SLURM_JOB_ID}" 'charmpp@6.10.2.sh'

sleep 20
