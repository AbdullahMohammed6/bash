import numpy as np
import os

NX = 30
NY = 110
NZ = 45
DZ = 6
tops = []

output_path = os.path.join("/path/flow/include/","FLOW.tops")

with open(output_path, "w") as f:
    f.write(f"TOPS\n")
    # for k in range(1, NZ+1):
    for j in range(1, NY+1):
        for i in range(1, NX+1):
                # z = (12140 + DZ*(k-1)
                #     - 25*np.exp(-((i-30)/18)**2 - ((j-110)/55)**2)
                #     + 0.08*(j-110)
                #     + 1*np.sin(i/14))
                z = (12140
                    - 100*np.exp(-((i-30)/18)**2 - ((j-110)/55)**2)
                    + 0.08*(j-110)
                    + 1*np.sin(i/14)
                    + 0.15*(i-30))

                f.write(f" {z:.3f}\n")
    f.write('/')









import numpy as np

# ======================
# Grid dimensions
# ======================
NX = 60
NY = 220
NZ = 85

DX = 40.0   # ft (example)
DY = 40.0   # ft
DZ = 2.0    # ft

# ======================
# Structural parameters
# ======================

# Anticline amplitude
A = 25.0

# Tilt gradients (safe slopes)
tilt_x = 0.03     # ft depth per grid index
tilt_y = 0.015

# Roughness amplitude
rough_amp = 1.0

# Grid center
ic = NX / 2.0
jc = NY / 2.0

# ======================
# Build structural surface S(i,j)
# ======================

S = np.zeros((NX, NY))

for j in range(NY):
    for i in range(NX):

        ii = i + 1
        jj = j + 1

        anticline = -A * np.exp(-((ii-ic)/18.0)**2
                                -((jj-jc)/55.0)**2)

        tilt = tilt_x*(ii-ic) + tilt_y*(jj-jc)

        rough = rough_amp*np.sin(ii/14.0)

        S[i, j] = 12140 + anticline + tilt + rough

# ======================
# Build full 3D Z array
# ======================

Z = np.zeros((NX, NY, NZ))

output_path = os.path.join("/path/flow/include/","FLOW.tops")

with open(output_path, "w") as f:
    f.write(f"TOPS\n")
    for k in range(NZ):
        Z[:, :, k] = S + k*DZ
        f.write(f"\n")
    f.write("/")

# ======================
# Generate TOPS keyword
# ======================

tops = Z[:, :, 0]









import numpy as np
import re


# -------------------------------------------------
# 1. Expand Eclipse compressed format (e.g. 10*0.25)
# -------------------------------------------------
def expand_eclipse_data(tokens):
    expanded = []
    for token in tokens:
        if '*' in token:
            n, val = token.split('*')
            expanded.extend([float(val)] * int(n))
        else:
            expanded.append(float(token))
    return np.array(expanded)


# -------------------------------------------------
# 2. Read PORO keyword from include file
# -------------------------------------------------
def read_poro_from_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    poro_data = []
    reading = False

    for line in lines:
        stripped = line.strip().upper()

        if stripped.startswith("PORO"):
            reading = True
            continue

        if reading:
            if '/' in stripped:
                stripped = stripped.replace('/', '')
                poro_data.extend(stripped.split())
                break
            poro_data.extend(stripped.split())

    return expand_eclipse_data(poro_data)


# -------------------------------------------------
# 3. Reshape to 3D (ECLIPSE ordering: I fastest)
# -------------------------------------------------
def reshape_to_3d(data, nx, ny, nz):
    return data.reshape((nz, ny, nx))


# -------------------------------------------------
# 4. Upscale XY using block averaging
# -------------------------------------------------
def upscale_xy_block_average(grid, factor_x=2, factor_y=2):
    nz, ny, nx = grid.shape
    new_nx = nx // factor_x
    new_ny = ny // factor_y

    reshaped = grid.reshape(
        nz,
        new_ny, factor_y,
        new_nx, factor_x
    )

    return reshaped.mean(axis=(2,4))


# -------------------------------------------------
# 5. Upscale Z using interpolation
# -------------------------------------------------
def upscale_z_interpolate(grid, new_nz):
    old_nz = grid.shape[0]

    z_old = np.linspace(0, 1, old_nz)
    z_new = np.linspace(0, 1, new_nz)

    new_grid = np.zeros((new_nz, grid.shape[1], grid.shape[2]))

    for j in range(grid.shape[1]):
        for i in range(grid.shape[2]):
            new_grid[:, j, i] = np.interp(z_new, z_old, grid[:, j, i])

    return new_grid


# -------------------------------------------------
# 6. Write new PORO include file
# -------------------------------------------------
def write_poro_include(filename, grid):
    flat = grid.flatten(order='C')

    with open(filename, 'w') as f:
        f.write("PORO\n")

        for i in range(0, len(flat), 6):
            line = " ".join(f"{v:.6f}" for v in flat[i:i+6])
            f.write(line + "\n")

        f.write("/\n")


# -------------------------------------------------
# 7. Main execution
# -------------------------------------------------
if __name__ == "__main__":

    input_file  = "path/flow/include/FLOWO.poro"
    output_file = "/path/flow/include/FLOW.poro"

    # Original and new dimensions
    nx_old, ny_old, nz_old = 60, 220, 85
    nx_new, ny_new, nz_new = 30, 110, 44

    # Read PORO
    poro = read_poro_from_file(input_file)

    if len(poro) != nx_old * ny_old * nz_old:
        raise ValueError("PORO size does not match original DIMENS.")

    grid = reshape_to_3d(poro, nx_old, ny_old, nz_old)

    # XY block average (2x2)
    grid_xy = upscale_xy_block_average(grid, factor_x=2, factor_y=2)

    # Z interpolation (85 -> 45)
    grid_final = upscale_z_interpolate(grid_xy, nz_new)

    # Write new include
    write_poro_include(output_file, grid_final)

    print("Upscaled PORO file written to:", output_file)


# Print in Eclipse format










import numpy as np


# -------------------------------------------------
# 1. Expand Eclipse compressed format (e.g. 10*100)
# -------------------------------------------------
def expand_eclipse_data(tokens):
    expanded = []
    for token in tokens:
        if '*' in token:
            n, val = token.split('*')
            expanded.extend([float(val)] * int(n))
        else:
            expanded.append(float(token))
    return np.array(expanded)


# -------------------------------------------------
# 2. Read PERMX keyword from include file
# -------------------------------------------------
def read_keyword_from_file(filename, keyword):
    with open(filename, 'r') as f:
        lines = f.readlines()

    data = []
    reading = False

    for line in lines:
        stripped = line.strip().upper()

        if stripped.startswith(keyword):
            reading = True
            continue

        if reading:
            if '/' in stripped:
                stripped = stripped.replace('/', '')
                data.extend(stripped.split())
                break
            data.extend(stripped.split())

    return expand_eclipse_data(data)


# -------------------------------------------------
# 3. Reshape to 3D (ECLIPSE ordering: I fastest)
# -------------------------------------------------
def reshape_to_3d(data, nx, ny, nz):
    return data.reshape((nz, ny, nx))


# -------------------------------------------------
# 4. Harmonic average in X (factor 2)
# -------------------------------------------------
def harmonic_average_x(grid, factor_x=2):
    nz, ny, nx = grid.shape
    new_nx = nx // factor_x

    # Prevent division by zero
    grid = np.where(grid <= 1e-12, 1e-12, grid)

    reshaped = grid.reshape(
        nz,
        ny,
        new_nx,
        factor_x
    )

    # Harmonic mean along X blocks
    harmonic = factor_x / np.sum(1.0 / reshaped, axis=3)

    return harmonic


# -------------------------------------------------
# 5. Arithmetic average in Y (factor 2)
# -------------------------------------------------
def arithmetic_average_y(grid, factor_y=2):
    nz, ny, nx = grid.shape
    new_ny = ny // factor_y

    reshaped = grid.reshape(
        nz,
        new_ny,
        factor_y,
        nx
    )

    return reshaped.mean(axis=2)


# -------------------------------------------------
# 6. Z interpolation (85 -> 45)
# -------------------------------------------------
def upscale_z_interpolate(grid, new_nz):
    old_nz = grid.shape[0]

    z_old = np.linspace(0, 1, old_nz)
    z_new = np.linspace(0, 1, new_nz)

    new_grid = np.zeros((new_nz, grid.shape[1], grid.shape[2]))

    for j in range(grid.shape[1]):
        for i in range(grid.shape[2]):
            new_grid[:, j, i] = np.interp(z_new, z_old, grid[:, j, i])

    return new_grid


# -------------------------------------------------
# 7. Write new include file
# -------------------------------------------------
def write_keyword_include(filename, keyword, grid):
    flat = grid.flatten(order='C')

    with open(filename, 'w') as f:
        f.write(f"{keyword}\n")

        for i in range(0, len(flat), 6):
            line = " ".join(f"{v:.6f}" for v in flat[i:i+6])
            f.write(line + "\n")

        f.write("/\n")


# -------------------------------------------------
# 8. Main
# -------------------------------------------------
if __name__ == "__main__":

    input_file  = "/path/flow/include/FLOWO.perm"
    output_file = "/path/flow/include/FLOW.perm"

    # Dimensions
    nx_old, ny_old, nz_old = 60, 220, 85
    nx_new, ny_new, nz_new = 30, 110, 44

    # Read PERMX
    permx = read_keyword_from_file(input_file, "PERMX")

    if len(permx) != nx_old * ny_old * nz_old:
        raise ValueError("PERMX size does not match original DIMENS.")

    grid = reshape_to_3d(permx, nx_old, ny_old, nz_old)

    # Harmonic in X
    grid_x = harmonic_average_x(grid, factor_x=2)

    # Arithmetic in Y
    grid_xy = arithmetic_average_y(grid_x, factor_y=2)

    # Z interpolation
    grid_final = upscale_z_interpolate(grid_xy, nz_new)

    # Write output
    write_keyword_include(output_file, "PERMX", grid_final)

    print("Upscaled PERMX file written to:", output_file)










import numpy as np

# =====================================================
# GRID PARAMETERS
# =====================================================
NX = 30
NY = 110
NZ = 44

DX = 250.0
DY = 100.0
DZ = 2.0   # constant vertical thickness (robust)

# =====================================================
# STRUCTURE PARAMETERS
# =====================================================
base_depth = 12100.0
anticline_amp = 200.0
tilt_x = 0.02
tilt_y = 0.01

ic = NX / 2.0
jc = NY / 2.0

# =====================================================
# BUILD STRUCTURAL SURFACE S(i,j)
# =====================================================
S = np.zeros((NX+1, NY+1))

for j in range(NY+1):
    for i in range(NX+1):

        anticline = -anticline_amp * np.exp(
            -((i-ic)/15.0)**2
            -((j-jc)/50.0)**2
        )

        tilt = tilt_x*(i-ic) + tilt_y*(j-jc)

        S[i, j] = base_depth + anticline + tilt

# =====================================================
# BUILD 3D NODE DEPTH ARRAY Z
# =====================================================
Z = np.zeros((NX+1, NY+1, NZ+1))

for k in range(NZ+1):
    Z[:, :, k] = S + k*DZ

# =====================================================
# HELPER: WRITE 8 VALUES PER LINE
# =====================================================
def write_8_per_line(f, values):
    count = 0
    for v in values:
        f.write(f"{v:.3f} ")
        count += 1
        if count == 8:
            f.write("\n")
            count = 0
    if count != 0:
        f.write("\n")

# =====================================================
# BUILD COORD
# =====================================================
coord_vals = []

for j in range(NY+1):
    for i in range(NX+1):

        x = i * DX
        y = j * DY

        z_top = Z[i, j, 0]
        z_bot = Z[i, j, NZ]

        if abs(z_top) > 1e8 or abs(z_bot) > 1e8:
            raise ValueError("Invalid coordinate value detected.")

        coord_vals.extend([x, y, z_top,
                           x, y, z_bot])

# Sanity check
expected_coord = (NX+1)*(NY+1)*6
assert len(coord_vals) == expected_coord

# =====================================================
# BUILD ZCORN (CORRECT ECLIPSE ORDER)
# =====================================================
zcorn_vals = []

for k in range(NZ):

    # -------- TOP OF LAYER k --------
    for j in range(NY):

        # Near top (z1,z2)
        for i in range(NX):
            zcorn_vals.append(Z[i, j, k])
            zcorn_vals.append(Z[i+1, j, k])

        # Far top (z3,z4)
        for i in range(NX):
            zcorn_vals.append(Z[i, j+1, k])
            zcorn_vals.append(Z[i+1, j+1, k])

    # -------- BOTTOM OF LAYER k --------
    for j in range(NY):

        # Near bottom (z5,z6)
        for i in range(NX):
            zcorn_vals.append(Z[i, j, k+1])
            zcorn_vals.append(Z[i+1, j, k+1])

        # Far bottom (z7,z8)
        for i in range(NX):
            zcorn_vals.append(Z[i, j+1, k+1])
            zcorn_vals.append(Z[i+1, j+1, k+1])

# Sanity check
expected_zcorn = 8 * NX * NY * NZ
assert len(zcorn_vals) == expected_zcorn

# =====================================================
# WRITE GRDECL FILE
# =====================================================
with open("include/FLOW.GRDECL", "w") as f:

    f.write("SPECGRID\n")
    f.write(f"{NX} {NY} {NZ} 1 F /\n\n")

    # COORD
    f.write("COORD\n")
    write_8_per_line(f, coord_vals)
    f.write("/\n\n")

    # ZCORN
    f.write("ZCORN\n")
    write_8_per_line(f, zcorn_vals)
    f.write("/\n\n")

    # ACTNUM
    f.write("ACTNUM\n")
    f.write(f"{NX*NY*NZ}*1 /\n")

print("Grid successfully written.")











