import random
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn import datasets
from sklearn.utils import shuffle

# Implementation of a feedforward neural network(MLP) to use it as an autoencoder for word embeddings
# Requirements: TensorFlow, Pandas, Sklearn, Numpy

# TO DO:
# 1. data processing to script
# 2. expand to 3 or 5 hidden layers
# 3. test on randomized vector

# set random seed value
RANDOM_SEED = 50
tf.set_random_seed(RANDOM_SEED)

def init_weights(shape):
	"""weight initialization
	Note: use random value from normal distribution
	"""
	weights = tf.random_normal(shape, stddev = 0.1)

	return tf.Variable(weights)

def forward(X, w_1, w_2, b_1, b_2):
	"""forward-propagation
	Note: propagate inputs X through network, return output from hidden layer as "new synthesized word embedding"
	"""
	h = tf.add(tf.matmul(X, w_1), b_1) # h: hidden layer (h = x * w_1 + b_1)
	y_predict = tf.add(tf.matmul(h, w_2), b_2) # y_predict: estimated output (y_hat = h * w_2 + b_2)

	return h, y_predict

def concatenate_all_data(d):
	"""data pre-processing
	Note: concatenate more than two word embeddings, by using the helper function "concatenate_two_data"
	"""
	d_tmp = concatenate_two_data(d[0], d[1])
	if (len(d) == 2):
		return d_tmp
	elif (len(d) > 2):
		for i in range(2,len(d)-1):
			d_tmp = concatenate_two_data(d_tmp, d[i])
		return d_tmp

def concatenate_two_data(d1, d2):
	"""data pre-processing
	Note: concatenate two word embeddings, assuming d1 > d2 (if not, switch order) & same number of columns.
	Dimension of final dataset will be same as d1. If a word exists in only one of embeddings, fill empty cell w/ mean value.
	"""
	if (d2.shape[0] > d1.shape[0]):
		concatenate_data(d2, d1)
	else: 
		result = pd.merge(d1, d2, how='left', on='text')
		result.fillna(result.mean(), inplace=True)
		# result.to_csv('data/result.csv')

	return result

def split_data(data):
	"""reading & splitting data
	Note: split data into training(0.9) and test set(0.1)
	"""
	train = data.sample(frac=0.9,random_state=RANDOM_SEED)
	test = data.drop(train.index)

	return train, test

def main():
	# load word embeddings
	govt = pd.read_csv('data/govt_40.csv', encoding='ISO-8859-1') #(19928, 101)
	books = pd.read_csv('data/books_40.csv', encoding='ISO-8859-1') #(17506,101)
	all_embeddings = [govt, books]
	input_data = concatenate_all_data(all_embeddings) #(19929,201)
	input_data = input_data[input_data.columns[2:]]
	input_data.to_csv('data/input_data.csv')

	# split data into training & testing sets
	train, test = split_data(input_data) # train: (17936,201)
	train_X = train
	train_y = train

	# split testing sets into validation & testing sets
	validation = test.sample(frac=0.5, random_state=RANDOM_SEED) # validation: (996, 201)
	test = test.drop(validation.index) # test: (996, 201)

	# set batch size
	batch = 200 # number of words in each batch => epoch: 100 iterations
	model_path = "model/model.ckpt" # path to save model

	# set hidden layer size
	x_size = train_X.shape[1] # number of input nodes 
	h_size = 100  # number of hidden nodes(dimension)
	y_size = train_y.shape[1] # number of outcomes

	# set tf graph input 
	X = tf.placeholder("float", shape=[None, x_size])
	y = tf.placeholder("float", shape=[None, y_size])

	# set model weights
	w_1 = init_weights((x_size, h_size)) 
	w_2 = init_weights((h_size, y_size))

	# set bias
	b_1 = tf.Variable(tf.ones([h_size]))
	b_2 = tf.Variable(tf.ones([y_size]))

	# forward propagation
	hidden_output, y_predict = forward(X, w_1, w_2, b_1, b_2) # hidden_output: synthesized word embedding

	# backward propagation
	error = tf.subtract(y, y_predict)
	mse = tf.reduce_mean(tf.square(error))
	update = tf.train.GradientDescentOptimizer(0.001).minimize(mse) # SGD step size: 0.001

	# create 'saver' op to save all variables
	saver = tf.train.Saver()

	# run stochastic gradient descent
	sess = tf.Session()
	init = tf.global_variables_initializer()

	with tf.Session() as sess:
		sess.run(init)

		tf.train.write_graph(sess.graph, "model/",'graph.pbtxt')

		# tf.summary.scalar("Mean Squared Error:", mse)
		# tf.summary.histogram('weight 1', w_1)
		# tf.summary.histogram('bias 1', b_1)
		# tf.summary.histogram('weight 2', w_2)
		# tf.summary.histogram('bias 2', b_2)
		# tf.summary.histogram("Hideen layer output", hidden_output)
		# summary_op = tf.summary.merge_all()
		# #summary_writer = tf.train.SummaryWriter('./tenIrisSave/logs',graph_def=sess.graph_def)
		# #summary_writer = tf.summary.FileWriter('data/',sess.graph)
		# saver = tf.train.Saver([w_1,b_1])

		print("...")

		for epoch in range(100): 
			# initialize variables
			total_mse = total_mse_test = total_mse_valid = 0
			train = shuffle(train)
			test = shuffle(test)
			train_X = train_y = train
			test_X = test_y = test
			validation_X = validation_y = validation
			last_train_batch = train_X.shape[0] % batch
			last_test_batch = test_X.shape[0] % batch
			last_validation_batch = validation_X.shape[0] % batch

			# compute training accuracy (average of L2 norm)
			for i in range(0, len(train_X), 200):
				if (i + batch < len(train_X)):
					batch_mse, __ = sess.run([mse,update], feed_dict={X: train_X[i: i+batch], y: train_y[i: i+batch]})
					i = i + batch
				else: # last batch
					batch_mse, __ = sess.run([mse,update], feed_dict={X: train_X[i:i+last_train_batch], y: train_y[i:i+last_train_batch]})
				total_mse = total_mse + batch_mse * batch
			train_accuracy = total_mse / len(train_X)

			# compute testing accuracy (average of L2 norm)
			for i in range(0, len(test_X), 200):
				if (i + batch < len(train_X)):
					batch_mse = sess.run(mse, feed_dict={X: test_X[i: i+batch], y: test_y[i: i+batch]})
					i = i + batch
				else:
					batch_mse = sess.run(mse, feed_dict={X: test_X[i: i+last_test_batch], y: test_y[i: i+last_test_batch]})
				total_mse_test = total_mse_test + batch_mse * batch
			test_accuracy = total_mse_test / len(test_X)

			# compute validation accuracy (average of L2 norm)
			for i in range(0, len(validation_X), 200):
				if (i + batch < len(train_X)):
					batch_mse = sess.run(mse, feed_dict={X: validation_X[i: i+batch], y: validation_y[i: i+batch]})
					i = i + batch
				else:
					batch_mse = sess.run(mse, feed_dict={X: validation_X[i: i+last_validation_batch], y: validation_y[i: i+last_validation_batch]})
				total_mse_valid = total_mse_valid + batch_mse * batch
			validation_accuracy = total_mse_valid / len(validation_X)

			print("Epoch = %d, train average MSE = %.2f%%, test average MSE = %.2f%%, validation average MSE = %.2f%%" % (epoch + 1, train_accuracy, test_accuracy, validation_accuracy))
			
		# save model 
		save_path = saver.save(sess, model_path)
		print("Model saved in file: %s" % save_path)

		# write file for GraphVisualizer
		file_writer = tf.summary.FileWriter('model/', sess.graph)

	  	# get output of hidden layer node("Variable_1") from TensorFlow session
		layer1_output = tf.get_default_graph().get_tensor_by_name("Variable_1:0")
		
		# save output as a new synthesized word embedding set
		syn_embed = sess.run(layer1_output) #(100,199)

		# close TensorFlow session
		sess.close()

		# write CSV file for a new embedding set
		print("New embedding saved with size of %s at %s" % (str(syn_embed.shape), 'data/syn_embed.csv'))
		pd.DataFrame(syn_embed).to_csv('data/syn_embed.csv')

		# print instruction to launch Tensorflow
		print("Run the Tensorflow with the command: %s" % ("tensorboard --logdir data/"))

if __name__ == '__main__':
	main()
