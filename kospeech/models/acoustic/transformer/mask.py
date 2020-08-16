import torch
from torch import Tensor
from typing import (
    Any,
    Optional
)


def get_pad_mask(inputs: Tensor, input_lengths: Optional[Any] = None, pad_id: int = None) -> Tensor:
    """
    Padding position is set to True, either use input_lengths or pad_id

    Examples::
        >>> get_pad_mask(inputs, input_lengths)
        [[0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
         [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
         [0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
         [0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
         [0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
         [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
         [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
         [0, 0, 0, 0, 0, 0, 1, 1, 1, 1]] x batch_size
    """
    assert (input_lengths is None and pad_id is not None) or (input_lengths is not None and pad_id is None)

    if input_lengths is not None:
        batch_size = inputs.size(0)
        pad_mask = inputs.new_zeros(inputs.size()[:-1])  # B x T

        for i in range(batch_size):
            pad_mask[i, input_lengths[i]:] = 1

    if pad_id is not None:
        assert inputs.dim() == 2
        pad_mask = inputs.eq(pad_id)

    return pad_mask.unsqueeze(-1).bool()


def get_subsequent_mask(inputs: Tensor) -> Tensor:
    """
    Makes subsequent masking like following:

    Examples::
        >>> get_subsequent_mask(inputs)
        [[0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
         [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
         [0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
         [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
         [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
         [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
         [0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
         [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
         [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]] x batch_size
    """

    batch_size, seq_length = inputs.size()
    subsequent_mask = torch.triu(torch.ones((seq_length, seq_length), device=inputs.device, dtype=torch.uint8), diagonal=1)
    subsequent_mask = subsequent_mask.unsqueeze(0).expand(batch_size, -1, -1)  # BxTxT

    return subsequent_mask.bool()


def get_attn_pad_mask(padded_input, input_lengths, expand_length):
    """ mask position is set to 1 """
    # N x Ti x 1
    non_pad_mask = get_pad_mask(padded_input, input_lengths=input_lengths).eq(False)
    # N x Ti, lt(1) like not operation
    pad_mask = non_pad_mask.squeeze(-1).lt(1)
    attn_mask = pad_mask.unsqueeze(1).expand(-1, expand_length, -1)
    return attn_mask


def get_attn_key_pad_mask(seq_k, seq_q, pad_idx):
    """ For masking out the padding part of key sequence. """

    # Expand to fit the shape of key query attention matrix.
    len_q = seq_q.size(1)
    padding_mask = seq_k.eq(pad_idx)
    padding_mask = padding_mask.unsqueeze(1).expand(-1, len_q, -1)  # b x lq x lk

    return padding_mask