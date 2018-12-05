import numpy as np

Nth_measurement = 10

############### Import key ##################

with open("../Data/Measurement_"+str(Nth_measurement)+"/key.txt", 'r') as f:
    key_hex = f.readlines()

key_header_hex_msb = '00' + key_hex[0][0:32]
key_header_hex_lsb ='01' + key_hex[0][32:64]
key_string = key_header_hex_msb.decode("hex") + key_header_hex_lsb.decode("hex")

################ Import plaintexts #################
with open('..\Data\Measurement_'+str(Nth_measurement)+'\pt_fpga.txt', 'r') as f:
    plaintexts = f.readlines()
plaintexts = [x.strip() for x in plaintexts] # remove \n at the end
nb_plaintexts  = len(plaintexts)
n_traces  = nb_plaintexts

pt_string = ['']*nb_plaintexts

i=0
for x in plaintexts:
	pt_string[i] = x.decode("hex")
	i = i + 1


#######
i=0
while i < n_traces:
	j=0
	while j < n_mean:
		h.write(pt_string[i])
		ciphertext[n_mean*i+j] = h.read(16).encode('hex')
		scope.write('CURVE?')
		traces[n_mean*i+j] = scope.read_raw()
		# traces[n_mean*i+j] = scope.query_binary_values('CURV?', datatype='d', is_big_endian=True)
		print str(i) + "/" + str(n_traces-1) + "  Capturing Traces ..."
		j = j + 1
	i = i + 1
	if i%1000==0:
		with open('../Data/Measurement_'+str(Nth_measurement)+'/traces.txt', "wb") as f :
			for x in traces:
				f.write(str(x))
		with open('../Data/Measurement_'+str(Nth_measurement)+'/ciphertext.txt', "wb") as f :
			for y in ciphertext:
				f.write(str(y))
				f.write('\n')
with open('../Data\Measurement_'+str(Nth_measurement)+'/scope_parameters.txt', "wb") as f :
	f.write(scope.query('WFMPRE:YMULT?'))
	f.write('\n')
	f.write(scope.query('WFMPRE:YZERO?'))
	f.write('\n')
	f.write(scope.query('WFMPRE:YOFF?'))
	f.write('\n')

