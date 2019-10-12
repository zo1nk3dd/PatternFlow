import tensorflow as tf

tf.compat.v1.enable_eager_execution() # Make eager execution available

# Function1 -- unique_inverse
def unique_inverse(image):
    """
    Find the indices of the unique tensor that reconstruct the input image.

    Parameters
    ----------
    image : tensor
            Input a tesnor(image) which has already be flatten(1-D)

    Returns
    -------
    inv_idx: tensor
           The indices to reconstruct the original value from the
        unique value of image(tensor).

    Examples
    --------
    >>> A = [1,4,5,5,2,10,2,3,4,3,9]
    >>> A = tf.convert_to_tensor(A)
    >>> print(unique_inverse(A))
    tf.Tensor([0 3 4 4 1 6 1 2 3 2 5], shape=(11,), dtype=int32)
    """
    
    # convert data type to tf.int32 (tf.uint8(Most common) --> tf.int32)
    image = tf.cast(image,dtype = tf.int32)
    # Sort the values in tensor and return index
    perm = tf.argsort(image)
    # get the value of tensor
    perm = perm.numpy()
    image = image.numpy()
    #array operation
    aux = image[perm]
    #create a zero tensor
    mask = tf.zeros(aux.shape, dtype=tf.bool)
    mask = mask.numpy()
    mask[:1] = True
    mask[1:] = aux[1:] != aux[:-1]
    # dtype convert to tf.int32
    k = tf.cast(mask,dtype = tf.int32)
    # Compute the cumulative sum of the tensor
    imask = tf.cumsum(k) - 1
    inv_idx = tf.zeros(mask.shape, dtype=tf.int32)
    inv_idx = inv_idx.numpy()
    inv_idx[perm] = imask
    # reconvert to tensor to return 
    inv_idx = tf.convert_to_tensor(inv_idx)
    return inv_idx
   

def _interpolate( dx_T, dy_T, x, name='interpolate' ):
    
    
    with tf.compat.v1.variable_scope(name):

        with tf.compat.v1.variable_scope('neighbors'):

            delVals = tf.subtract(dx_T, x)
            ind_1   = tf.argmax(tf.sign( delVals ))
            ind_0   = ind_1 - 1

        with tf.compat.v1.variable_scope('calculation'):

            value   = tf.cond( x[0] <= dx_T[0], 
                              lambda : dy_T[:1], 
                              lambda : tf.cond( 
                                     x[0] >= dx_T[-1], 
                                     lambda : dy_T[-1:],
                                     lambda : (dy_T[ind_0] +                
                                               (dy_T[ind_1] - dy_T[ind_0])  
                                               *(x-dx_T[ind_0])/            
                                               (dx_T[ind_1]-dx_T[ind_0]))
                             ))

        result = tf.multiply(value[0], 1, name='y')

    return result

def _match_cumulative_cdf(source, template):
    source_flatten = tf.reshape(source,[-1])
    template_flatten = tf.reshape(template,[-1])
    #sort the tensor
    source_flatten_sort = tf.cast(source_flatten ,dtype =tf.int32)
    source_flatten_sort = tf.sort(source_flatten_sort)
    template_flatten = tf.cast(template_flatten ,dtype =tf.int32)
    template_flatten = tf.sort(template_flatten)

    src_values, src_unique_indices, src_counts = tf.unique_with_counts(source_flatten_sort)
    #bianhua
    src_indice = unique_inverse(source_flatten)
    #
    tmpl_values,tmpl_unique_indices,tmpl_counts = tf.unique_with_counts(template_flatten)
    tmpl_values = tf.cast(tmpl_values,dtype=tf.float64)
    source_size = tf.size(source_flatten)
    template_size = tf.size(template_flatten)
    src_quantiles = tf.cumsum(src_counts) / source_size
    tmpl_quantiles = tf.cumsum(tmpl_counts) / template_size
    #interpolate
    interp_a_values = []
    for i in src_quantiles.numpy():

        interp_a_values.append(_interpolate(tmpl_quantiles, tmpl_values, tf.constant([i])))
    interp_a_values = tf.convert_to_tensor(interp_a_values).numpy()
    guodu = interp_a_values[src_indice]
    #convert_to_tensor
    guodu = tf.convert_to_tensor(guodu)
    result = tf.reshape(guodu,tf.shape(source))
    return result

    
def match_histograms(image, reference, multichannel=False):
     
    if tf.rank(image).numpy() != tf.rank(reference).numpy():
        raise ValueError('Image and reference must have the same number of channels.')
    if multichannel:
        if image.shape[-1] != reference.shape[-1]:
            raise ValueError('Number of channels in the input image and reference '
                             'image must match!')

        
        matched_channel = []
    
        for channel in range(image.shape[-1]):
            matched_channel.append(_match_cumulative_cdf(image[..., channel], reference[..., channel]))
            
        matched = tf.stack([matched_channel[0],matched_channel[1],matched_channel[2]], axis=2)

        matched = matched/255.
    
    else:
        matched = _match_cumulative_cdf(image, reference)
        matched = matched/255.
    return matched
