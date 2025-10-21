use anchor_lang::prelude::*;
use sha3::{Digest, Keccak256};

declare_id!("Janu5BridGeAdApTer111111111111111111111111111");

#[program]
pub mod janus_bridge_adapter {
    use super::*;

    pub fn process_message(ctx: Context<ProcessMessage>, message: Vec<u8>, proof: Vec<u8>) -> Result<()> {
        let st = &mut ctx.accounts.state;
        require!(verify_bridge_proof(&proof, &message), JanusError::InvalidProof);

        let message_id = keccak(&message);
        require!(!st.seen.contains_key(&message_id), JanusError::Replay);
        st.seen.insert(message_id, true);

        let (dst_program, ix_data) = split_dst_and_ix(&message)?;
        invoke_ix(dst_program, ix_data, &ctx.remaining_accounts)?;
        emit!(ExecutionEvent { message_id });

        Ok(())
    }

    pub fn set_registry(ctx: Context<SetRegistry>, new_registry: Pubkey) -> Result<()> {
        let st = &mut ctx.accounts.state;
        require!(ctx.accounts.authority.key() == st.authority, JanusError::Unauthorized);
        st.registry = new_registry;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ProcessMessage<'info> {
    #[account(mut, seeds = [b"state"], bump)]
    pub state: Account<'info, AdapterState>,
}

#[derive(Accounts)]
pub struct SetRegistry<'info> {
    #[account(mut, seeds = [b"state"], bump)]
    pub state: Account<'info, AdapterState>,
    pub authority: Signer<'info>,
}

#[account]
pub struct AdapterState {
    pub authority: Pubkey,
    pub registry: Pubkey,
    pub seen: BTreeMap<[u8; 32], bool>,
}

#[event]
pub struct ExecutionEvent {
    pub message_id: [u8; 32],
}

#[error_code]
pub enum JanusError {
    #[msg("Invalid bridge proof")] InvalidProof,
    #[msg("Message already processed (replay)")] Replay,
    #[msg("Unauthorized")] Unauthorized,
}

fn verify_bridge_proof(_proof: &Vec<u8>, _message: &Vec<u8>) -> bool { true }

fn split_dst_and_ix(message: &Vec<u8>) -> Result<(Pubkey, Vec<u8>)> {
    if message.len() < 32 { return err!(JanusError::InvalidProof); }
    let mut key_bytes = [0u8; 32];
    key_bytes.copy_from_slice(&message[0..32]);
    Ok((Pubkey::new_from_array(key_bytes), message[32..].to_vec()))
}

fn invoke_ix(dst: Pubkey, ix_data: Vec<u8>, remaining: &[AccountInfo]) -> Result<()> {
    let ix = anchor_lang::solana_program::instruction::Instruction {
        program_id: dst,
        accounts: vec![],
        data: ix_data,
    };
    anchor_lang::solana_program::program::invoke(&ix, remaining)?;
    Ok(())
}

fn keccak(data: &Vec<u8>) -> [u8; 32] {
    let mut hasher = Keccak256::new();
    hasher.update(data);
    let out = hasher.finalize();
    let mut arr = [0u8; 32];
    arr.copy_from_slice(&out);
    arr
}
